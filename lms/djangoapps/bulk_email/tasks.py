"""
This module contains celery task functions for handling the sending of bulk email
to a course.
"""
import math
import re
import time

from dogapi import dog_stats_api
from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMultiAlternatives, get_connection
from django.http import Http404
from celery import task, current_task
from celery.utils.log import get_task_logger
from django.core.urlresolvers import reverse

from bulk_email.models import (
    CourseEmail, Optout, CourseEmailTemplate,
    SEND_TO_MYSELF, SEND_TO_STAFF, SEND_TO_ALL,
)
from courseware.access import _course_staff_group_name, _course_instructor_group_name
from courseware.courses import get_course_by_id, course_image_url

log = get_task_logger(__name__)


@task(default_retry_delay=10, max_retries=5)  # pylint: disable=E1102
def delegate_email_batches(email_id, user_id):
    """
    Delegates emails by querying for the list of recipients who should
    get the mail, chopping up into batches of settings.EMAILS_PER_TASK size,
    and queueing up worker jobs.

    Returns the number of batches (workers) kicked off.
    """
    try:
        email_obj = CourseEmail.objects.get(id=email_id)
    except CourseEmail.DoesNotExist as exc:
        # The retry behavior here is necessary because of a race condition between the commit of the transaction
        # that creates this CourseEmail row and the celery pipeline that starts this task.
        # We might possibly want to move the blocking into the view function rather than have it in this task.
        log.warning("Failed to get CourseEmail with id %s, retry %d", email_id, current_task.request.retries)
        raise delegate_email_batches.retry(arg=[email_id, user_id], exc=exc)

    to_option = email_obj.to_option
    course_id = email_obj.course_id

    try:
        course = get_course_by_id(course_id, depth=1)
    except Http404 as exc:
        log.exception("get_course_by_id failed: %s", exc.args[0])
        raise Exception("get_course_by_id failed: " + exc.args[0])

    course_url = 'https://{}{}'.format(
        settings.SITE_NAME,
        reverse('course_root', kwargs={'course_id': course_id})
    )
    image_url = 'https://{}{}'.format(settings.SITE_NAME, course_image_url(course))

    if to_option == SEND_TO_MYSELF:
        recipient_qset = User.objects.filter(id=user_id)
    elif to_option == SEND_TO_ALL or to_option == SEND_TO_STAFF:
        staff_grpname = _course_staff_group_name(course.location)
        staff_group, _ = Group.objects.get_or_create(name=staff_grpname)
        staff_qset = staff_group.user_set.all()
        instructor_grpname = _course_instructor_group_name(course.location)
        instructor_group, _ = Group.objects.get_or_create(name=instructor_grpname)
        instructor_qset = instructor_group.user_set.all()
        recipient_qset = staff_qset | instructor_qset

        if to_option == SEND_TO_ALL:
            enrollment_qset = User.objects.filter(courseenrollment__course_id=course_id,
                                                  courseenrollment__is_active=True)
            recipient_qset = recipient_qset | enrollment_qset
        recipient_qset = recipient_qset.distinct()
    else:
        log.error("Unexpected bulk email TO_OPTION found: %s", to_option)
        raise Exception("Unexpected bulk email TO_OPTION found: {0}".format(to_option))

    recipient_qset = recipient_qset.order_by('pk')
    total_num_emails = recipient_qset.count()
    num_queries = int(math.ceil(float(total_num_emails) / float(settings.EMAILS_PER_QUERY)))
    last_pk = recipient_qset[0].pk - 1
    num_workers = 0
    for _ in range(num_queries):
        recipient_sublist = list(recipient_qset.order_by('pk').filter(pk__gt=last_pk)
                                 .values('profile__name', 'email', 'pk')[:settings.EMAILS_PER_QUERY])
        last_pk = recipient_sublist[-1]['pk']
        num_emails_this_query = len(recipient_sublist)
        num_tasks_this_query = int(math.ceil(float(num_emails_this_query) / float(settings.EMAILS_PER_TASK)))
        chunk = int(math.ceil(float(num_emails_this_query) / float(num_tasks_this_query)))
        for i in range(num_tasks_this_query):
            to_list = recipient_sublist[i * chunk:i * chunk + chunk]
            course_email.delay(
                email_id,
                to_list,
                course.display_name,
                course_url,
                image_url,
                False
            )
        num_workers += num_tasks_this_query
    return num_workers


@task(default_retry_delay=15, max_retries=5)  # pylint: disable=E1102
def course_email(email_id, to_list, course_title, course_url, image_url, throttle=False):
    """
    Takes a primary id for a CourseEmail object and a 'to_list' of recipient objects--keys are
    'profile__name', 'email' (address), and 'pk' (in the user table).
    course_title, course_url, and image_url are to memoize course properties and save lookups.

    Sends to all addresses contained in to_list.  Emails are sent multi-part, in both plain
    text and html.
    """
    with dog_stats_api.timer('course_email.single_task.time.overall', tags=[_statsd_tag(course_title)]):
        _send_course_email(email_id, to_list, course_title, course_url, image_url, throttle)

def _send_course_email(email_id, to_list, course_title, course_url, image_url, throttle):
    """
    Performs the email sending task.
    """
    try:
        msg = CourseEmail.objects.get(id=email_id)
    except CourseEmail.DoesNotExist:
        log.exception("Could not find email id:{} to send.".format(email_id))
        raise

    # exclude optouts
    optouts = (Optout.objects.filter(course_id=msg.course_id,
                                     user__in=[i['pk'] for i in to_list])
                             .values_list('user__email', flat=True))

    optouts = set(optouts)
    num_optout = len(optouts)

    to_list = [recipient for recipient in to_list if recipient['email'] not in optouts]

    subject = "[" + course_title + "] " + msg.subject

    course_title_no_quotes = re.sub(r'"', '', course_title)
    from_addr = '"{0}" Course Staff <{1}>'.format(course_title_no_quotes, settings.DEFAULT_BULK_FROM_EMAIL)

    course_email_template = CourseEmailTemplate.get_template()

    try:
        connection = get_connection()
        connection.open()
        num_sent = 0
        num_error = 0

        # Define context values to use in all course emails:
        email_context = {
            'name': '',
            'email': '',
            'course_title': course_title,
            'course_url': course_url,
            'course_image_url': image_url,
            'account_settings_url': 'https://{}{}'.format(settings.SITE_NAME, reverse('dashboard')),
            'platform_name': settings.PLATFORM_NAME,
        }

        while to_list:
            # Update context with user-specific values:
            email = to_list[-1]['email']
            email_context['email'] = email
            email_context['name'] = to_list[-1]['profile__name']

            # Construct message content using templates and context:
            plaintext_msg = course_email_template.render_plaintext(msg.text_message, email_context)
            html_msg = course_email_template.render_htmltext(msg.html_message, email_context)

            # Create email:
            email_msg = EmailMultiAlternatives(
                subject,
                plaintext_msg,
                from_addr,
                [email],
                connection=connection
            )
            email_msg.attach_alternative(html_msg, 'text/html')

            # Throttle if we tried a few times and got the rate limiter
            if throttle or current_task.request.retries > 0:
                time.sleep(0.2)

            try:
                with dog_stats_api.timer('course_email.single_send.time.overall', tags=[_statsd_tag(course_title)]):
                    connection.send_messages([email_msg])

                dog_stats_api.increment('course_email.sent', tags=[_statsd_tag(course_title)])

                log.info('Email with id %s sent to %s', email_id, email)
                num_sent += 1
            except SMTPDataError as exc:
                # According to SMTP spec, we'll retry error codes in the 4xx range.  5xx range indicates hard failure
                if exc.smtp_code >= 400 and exc.smtp_code < 500:
                    # This will cause the outer handler to catch the exception and retry the entire task
                    raise exc
                else:
                    # This will fall through and not retry the message, since it will be popped
                    log.warning('Email with id %s not delivered to %s due to error %s', email_id, email, exc.smtp_error)

                    dog_stats_api.increment('course_email.error', tags=[_statsd_tag(course_title)])

                    num_error += 1

            to_list.pop()

        connection.close()
        return course_email_result(num_sent, num_error, num_optout)

    except (SMTPDataError, SMTPConnectError, SMTPServerDisconnected) as exc:
        # Error caught here cause the email to be retried.  The entire task is actually retried without popping the list
        # Reasoning is that all of these errors may be temporary condition.
        log.warning('Email with id %d not delivered due to temporary error %s, retrying send to %d recipients',
                    email_id, exc, len(to_list))
        raise course_email.retry(
            arg=[
                email_id,
                to_list,
                course_title,
                course_url,
                image_url,
                current_task.request.retries > 0
            ],
            exc=exc,
            countdown=(2 ** current_task.request.retries) * 15
        )
    except:
        log.exception('Email with id %d caused course_email task to fail with uncaught exception. To list: %s',
                      email_id,
                      [i['email'] for i in to_list])
        # Close the connection before we exit
        connection.close()
        raise


# This string format code is wrapped in this function to allow mocking for a unit test
def course_email_result(num_sent, num_error, num_optout):
    """Return the formatted result of course_email sending."""
    return "Sent {0}, Fail {1}, Optout {2}".format(num_sent, num_error, num_optout)


def _statsd_tag(course_title):
    """
    Calculate the tag we will use for DataDog.
    """
    tag = "course_email:{0}".format(course_title)
    return tag[:200]
