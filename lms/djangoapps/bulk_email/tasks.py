"""
This module contains celery task functions for handling the sending of bulk email
to a course.
"""
import math
import re
from uuid import uuid4
from time import time, sleep
import json

from dogapi import dog_stats_api
from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError

from celery import task, current_task, group
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMultiAlternatives, get_connection
from django.http import Http404
from django.core.urlresolvers import reverse

from bulk_email.models import (
    CourseEmail, Optout, CourseEmailTemplate,
    SEND_TO_MYSELF, SEND_TO_STAFF, SEND_TO_ALL,
)
from courseware.access import _course_staff_group_name, _course_instructor_group_name
from courseware.courses import get_course_by_id, course_image_url
from instructor_task.models import InstructorTask, PROGRESS, QUEUING

log = get_task_logger(__name__)


def get_recipient_queryset(user_id, to_option, course_id, course_location):
    """
    Generates a query set corresponding to the requested category.

    `to_option` is either SEND_TO_MYSELF, SEND_TO_STAFF, or SEND_TO_ALL.
    """
    if to_option == SEND_TO_MYSELF:
        recipient_qset = User.objects.filter(id=user_id)
    elif to_option == SEND_TO_ALL or to_option == SEND_TO_STAFF:
        staff_grpname = _course_staff_group_name(course_location)
        staff_group, _ = Group.objects.get_or_create(name=staff_grpname)
        staff_qset = staff_group.user_set.all()
        instructor_grpname = _course_instructor_group_name(course_location)
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
    return recipient_qset


def get_course_email_context(course):
    """
    Returns context arguments to apply to all emails, independent of recipient.
    """
    course_id = course.id
    course_title = course.display_name
    course_url = 'https://{}{}'.format(
        settings.SITE_NAME,
        reverse('course_root', kwargs={'course_id': course_id})
    )
    image_url = 'https://{}{}'.format(settings.SITE_NAME, course_image_url(course))
    email_context = {
        'course_title': course_title,
        'course_url': course_url,
        'course_image_url': image_url,
        'account_settings_url': 'https://{}{}'.format(settings.SITE_NAME, reverse('dashboard')),
        'platform_name': settings.PLATFORM_NAME,
    }
    return email_context


def perform_delegate_email_batches(entry_id, course_id, task_input, action_name):
    """
    Delegates emails by querying for the list of recipients who should
    get the mail, chopping up into batches of settings.EMAILS_PER_TASK size,
    and queueing up worker jobs.

    Returns the number of batches (workers) kicked off.
    """
    entry = InstructorTask.objects.get(pk=entry_id)
    # get inputs to use in this task from the entry:
    #task_id = entry.task_id
    user_id = entry.requester.id

    # TODO: check this against argument passed in?
    # course_id = entry.course_id

    email_id = task_input['email_id']
    try:
        email_obj = CourseEmail.objects.get(id=email_id)
    except CourseEmail.DoesNotExist as exc:
        # The retry behavior here is necessary because of a race condition between the commit of the transaction
        # that creates this CourseEmail row and the celery pipeline that starts this task.
        # We might possibly want to move the blocking into the view function rather than have it in this task.
#        log.warning("Failed to get CourseEmail with id %s, retry %d", email_id, current_task.request.retries)
#        raise delegate_email_batches.retry(arg=[email_id, user_id], exc=exc)
        log.warning("Failed to get CourseEmail with id %s", email_id)
        raise

    to_option = email_obj.to_option

    # TODO: instead of fetching from email object, compare instead to
    # confirm that they match, and raise an exception if they don't.
    # course_id = email_obj.course_id

    try:
        course = get_course_by_id(course_id, depth=1)
    except Http404 as exc:
        log.exception("get_course_by_id failed: %s", exc.args[0])
        raise Exception("get_course_by_id failed: " + exc.args[0])

    global_email_context = get_course_email_context(course)
    recipient_qset = get_recipient_queryset(user_id, to_option, course_id, course.location)
    total_num_emails = recipient_qset.count()

    # At this point, we have some status that we can report, as to the magnitude of the overall
    # task.  That is, we know the total.  Set that, and our subtasks should work towards that goal.
    # Note that we add start_time in here, so that it can be used
    # by subtasks to calculate duration_ms values:
    progress = {'action_name': action_name,
                'attempted': 0,
                'updated': 0,
                'total': total_num_emails,
                'duration_ms': int(0),
                'start_time': time(),
                }

    num_queries = int(math.ceil(float(total_num_emails) / float(settings.EMAILS_PER_QUERY)))
    last_pk = recipient_qset[0].pk - 1
    num_workers = 0
    task_list = []
    subtask_id_list = []
    for _ in range(num_queries):
        # Note that if we were doing this for regrading we probably only need 'pk', and not
        # either profile__name or email.  That's because we'll have to do
        # a lot more work in the individual regrade for each user, but using user_id as a key.
        # TODO: figure out how to pass these values as an argument, when refactoring this code.
        recipient_sublist = list(recipient_qset.order_by('pk').filter(pk__gt=last_pk)
                                 .values('profile__name', 'email', 'pk')[:settings.EMAILS_PER_QUERY])
        last_pk = recipient_sublist[-1]['pk']
        num_emails_this_query = len(recipient_sublist)
        num_tasks_this_query = int(math.ceil(float(num_emails_this_query) / float(settings.EMAILS_PER_TASK)))
        chunk = int(math.ceil(float(num_emails_this_query) / float(num_tasks_this_query)))
        for i in range(num_tasks_this_query):
            to_list = recipient_sublist[i * chunk:i * chunk + chunk]
            subtask_id = str(uuid4())
            subtask_id_list.append(subtask_id)
            task_list.append(send_course_email.subtask((
                email_id,
                to_list,
                global_email_context,
                False
            ), task_id=subtask_id
            ))
        num_workers += num_tasks_this_query

    # Before we actually start running the tasks we've defined,
    # the InstructorTask needs to be updated with their information.
    # So at this point, we need to update the InstructorTask object here,
    # not in the return.
    entry.task_output = InstructorTask.create_output_for_success(progress)

    # TODO: the monitoring may need to track a different value here to know
    # that it shouldn't go to the InstructorTask's task's Result for its
    # progress.  It might be that this is getting saved.
    # It might be enough, on the other hand, for the monitoring code to see
    # that there are subtasks, and that it can scan these for the overall
    # status.  (And that it shouldn't clobber the progress that is being
    # accumulated.)  If there are no subtasks, then work as is current.
    entry.task_state = PROGRESS

    # now write out the subtasks information.
    subtask_status = dict.fromkeys(subtask_id_list, QUEUING)
    entry.subtasks = json.dumps(subtask_status)

    # and save the entry immediately, before any subtasks actually start work:
    entry.save_now()

    # now group the subtasks, and start them running:
    task_group = group(task_list)
    task_group_result = task_group.apply_async()

    # ISSUE: we can return this result now, but it's not really the result for this task.
    # So if we use the task_id to fetch a task result, we won't get this one.  But it
    # might still work.  The caller just has to hold onto this, and access it in some way.
    # Ugh.  That seems unlikely...
    # return task_group_result

    # Still want to return progress here, as this is what will be stored in the
    # AsyncResult for the parent task as its return value.
    # TODO: Humph.  But it will be marked as SUCCEEDED.  And have
    # this return value as it's "result".  So be it.  The InstructorTask
    # will not match, because it will have different info.
    return progress


@task(default_retry_delay=15, max_retries=5)  # pylint: disable=E1102
def send_course_email(email_id, to_list, global_email_context, throttle=False):
    """
    Takes a primary id for a CourseEmail object and a 'to_list' of recipient objects--keys are
    'profile__name', 'email' (address), and 'pk' (in the user table).
    course_title, course_url, and image_url are to memoize course properties and save lookups.

    Sends to all addresses contained in to_list.  Emails are sent multi-part, in both plain
    text and html.
    """
    course_title = global_email_context['course_title']
    with dog_stats_api.timer('course_email.single_task.time.overall', tags=[_statsd_tag(course_title)]):
        _send_course_email(email_id, to_list, global_email_context, throttle)


def _send_course_email(email_id, to_list, global_email_context, throttle):
    """
    Performs the email sending task.
    """
    try:
        course_email = CourseEmail.objects.get(id=email_id)
    except CourseEmail.DoesNotExist:
        log.exception("Could not find email id:{} to send.".format(email_id))
        raise

    # exclude optouts
    optouts = (Optout.objects.filter(course_id=course_email.course_id,
                                     user__in=[i['pk'] for i in to_list])
                             .values_list('user__email', flat=True))

    optouts = set(optouts)
    num_optout = len(optouts)

    to_list = [recipient for recipient in to_list if recipient['email'] not in optouts]

    course_title = global_email_context['course_title']
    subject = "[" + course_title + "] " + course_email.subject
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
            'email': ''
        }
        email_context.update(global_email_context)

        while to_list:
            # Update context with user-specific values:
            email = to_list[-1]['email']
            email_context['email'] = email
            email_context['name'] = to_list[-1]['profile__name']

            # Construct message content using templates and context:
            plaintext_msg = course_email_template.render_plaintext(course_email.text_message, email_context)
            html_msg = course_email_template.render_htmltext(course_email.html_message, email_context)

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
                sleep(0.2)

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
        raise send_course_email.retry(
            arg=[
                email_id,
                to_list,
                global_email_context,
                current_task.request.retries > 0
            ],
            exc=exc,
            countdown=(2 ** current_task.request.retries) * 15
        )
    except:
        log.exception('Email with id %d caused send_course_email task to fail with uncaught exception. To list: %s',
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
