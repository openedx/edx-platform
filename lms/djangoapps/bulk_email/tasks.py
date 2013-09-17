"""
This module contains celery task functions for handling the sending of bulk email
to a course.
"""
import math
import re
from uuid import uuid4
from time import time, sleep
import json
from sys import exc_info
from traceback import format_exc

from dogapi import dog_stats_api
from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError

from celery import task, current_task, group
from celery.utils.log import get_task_logger
from celery.states import SUCCESS, FAILURE

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMultiAlternatives, get_connection
from django.http import Http404
from django.core.urlresolvers import reverse
from django.db import transaction

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
        # The CourseEmail object should be committed in the view function before the task
        # is submitted and reaches this point.  It is possible to add retry behavior here,
        # to keep trying until the object is actually committed by the view function's return,
        # but it's cleaner to just expect to be done.
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

    log.info("Preparing to queue emails to %d recipient(s) for course %s, email %s, to_option %s",
             total_num_emails, course_id, email_id, to_option)

    # At this point, we have some status that we can report, as to the magnitude of the overall
    # task.  That is, we know the total.  Set that, and our subtasks should work towards that goal.
    # Note that we add start_time in here, so that it can be used
    # by subtasks to calculate duration_ms values:
    progress = {'action_name': action_name,
                'attempted': 0,
                'failed': 0,
                'skipped': 0,
                'succeeded': 0,
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
                entry_id,
                email_id,
                to_list,
                global_email_context,
                False
            ), task_id=subtask_id
            ))
        num_workers += num_tasks_this_query

    # Before we actually start running the tasks we've defined,
    # the InstructorTask needs to be updated with their information.
    # So we update the InstructorTask object here, not in the return.
    # The monitoring code knows that it shouldn't go to the InstructorTask's task's
    # Result for its progress when there are subtasks.  So we accumulate
    # the results of each subtask as it completes into the InstructorTask.
    entry.task_output = InstructorTask.create_output_for_success(progress)
    entry.task_state = PROGRESS

    # now write out the subtasks information.
    num_subtasks = len(subtask_id_list)
    subtask_status = dict.fromkeys(subtask_id_list, QUEUING)
    subtask_dict = {'total': num_subtasks, 'succeeded': 0, 'failed': 0, 'status': subtask_status}
    entry.subtasks = json.dumps(subtask_dict)

    # and save the entry immediately, before any subtasks actually start work:
    entry.save_now()

    log.info("Preparing to queue %d email tasks for course %s, email %s, to %s",
             num_subtasks, course_id, email_id, to_option)

    # now group the subtasks, and start them running:
    task_group = group(task_list)
    task_group.apply_async()

    # We want to return progress here, as this is what will be stored in the
    # AsyncResult for the parent task as its return value.
    # The Result will then be marked as SUCCEEDED, and have this return value as it's "result".
    # That's okay, for the InstructorTask will have the "real" status.
    return progress


def _get_current_task():
    """Stub to make it easier to test without actually running Celery"""
    return current_task


@transaction.commit_manually
def _update_subtask_status(entry_id, current_task_id, status, subtask_result):
    """
    Update the status of the subtask in the parent InstructorTask object tracking its progress.
    """
    log.info("Preparing to update status for email subtask %s for instructor task %d with status %s",
             current_task_id, entry_id, subtask_result)

    try:
        entry = InstructorTask.objects.select_for_update().get(pk=entry_id)
        subtask_dict = json.loads(entry.subtasks)
        subtask_status = subtask_dict['status']
        if current_task_id not in subtask_status:
            # unexpected error -- raise an exception?
            log.warning("Unexpected task_id '%s': unable to update status for email subtask of instructor task %d",
             current_task_id, entry_id)
            pass
        subtask_status[current_task_id] = status
        # now update the parent task progress
        task_progress = json.loads(entry.task_output)
        start_time = task_progress['start_time']
        task_progress['duration_ms'] = int((time() - start_time) * 1000)
        if subtask_result is not None:
            for statname in ['attempted', 'succeeded', 'failed', 'skipped']:
                task_progress[statname] += subtask_result[statname]
        # now figure out if we're actually done (i.e. this is the last task to complete)
        # (This might be easier by just maintaining a counter, rather than scanning the
        # entire subtask_status dict.)
        if status == SUCCESS:
            subtask_dict['succeeded'] += 1
        else:
            subtask_dict['failed'] += 1
        num_remaining = subtask_dict['total'] - subtask_dict['succeeded'] - subtask_dict['failed']
        if num_remaining <= 0:
            # we're done with the last task: update the parent status to indicate that:
            entry.task_state = SUCCESS
        entry.subtasks = json.dumps(subtask_dict)
        entry.task_output = InstructorTask.create_output_for_success(task_progress)

        log.info("Task output updated to %s for email subtask %s of instructor task %d",
                 entry.task_output, current_task_id, entry_id)

        log.info("about to save....")
        entry.save()
    except:
        log.exception("Unexpected error while updating InstructorTask.")
        transaction.rollback()
    else:
        log.info("about to commit....")
        transaction.commit()


@task(default_retry_delay=15, max_retries=5)  # pylint: disable=E1102
def send_course_email(entry_id, email_id, to_list, global_email_context, throttle=False):
    """
    Takes a primary id for a CourseEmail object and a 'to_list' of recipient objects--keys are
    'profile__name', 'email' (address), and 'pk' (in the user table).
    course_title, course_url, and image_url are to memoize course properties and save lookups.

    Sends to all addresses contained in to_list.  Emails are sent multi-part, in both plain
    text and html.
    """
    # Get entry here, as a sanity check that it actually exists.  We won't actually do anything
    # with it right away.
    InstructorTask.objects.get(pk=entry_id)
    current_task_id = _get_current_task().request.id

    log.info("Preparing to send email as subtask %s for instructor task %d",
             current_task_id, entry_id)

    try:
        course_title = global_email_context['course_title']
        with dog_stats_api.timer('course_email.single_task.time.overall', tags=[_statsd_tag(course_title)]):
            course_email_result = _send_course_email(email_id, to_list, global_email_context, throttle)
        # Assume that if we get here without a raise, the task was successful.
        # Update the InstructorTask object that is storing its progress.
        _update_subtask_status(entry_id, current_task_id, SUCCESS, course_email_result)

    except Exception:
        # try to write out the failure to the entry before failing
        _, exception, traceback = exc_info()
        traceback_string = format_exc(traceback) if traceback is not None else ''
        log.warning("background task (%s) failed: %s %s", current_task_id, exception, traceback_string)
        _update_subtask_status(entry_id, current_task_id, FAILURE, None)
        raise

    return course_email_result


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
                log.info('Email with id %s to be sent to %s', email_id, email)

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
        # TODO: figure out how to get (or persist) real statistics for this task, so that reflects progress
        # made over multiple retries.
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


def course_email_result(num_sent, num_error, num_optout):
    """Return the result of course_email sending as a dict (not a string)."""
    attempted = num_sent + num_error
    return {'attempted': attempted, 'succeeded': num_sent, 'skipped': num_optout, 'failed': num_error}


def _statsd_tag(course_title):
    """
    Calculate the tag we will use for DataDog.
    """
    tag = "course_email:{0}".format(course_title)
    return tag[:200]
