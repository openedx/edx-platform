"""
This module contains celery task functions for handling the sending of bulk email
to a course.
"""
import math
import re
import random
from uuid import uuid4
from time import sleep

from sys import exc_info
from traceback import format_exc

from dogapi import dog_stats_api
from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError
from boto.ses.exceptions import SESDailyQuotaExceededError, SESMaxSendingRateExceededError
from boto.exception import AWSConnectionError

from celery import task, current_task, group
from celery.utils.log import get_task_logger
from celery.states import SUCCESS, FAILURE, RETRY
from celery.exceptions import RetryTaskError

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
from instructor_task.models import InstructorTask
from instructor_task.subtasks import (
    update_subtask_status,
    create_subtask_result,
    increment_subtask_result,
    update_instructor_task_for_subtasks,
)

log = get_task_logger(__name__)


# Exceptions that, if caught, should cause the task to be re-tried.
# These errors will be caught a maximum of 5 times before the task fails.
RETRY_ERRORS = (SMTPDataError, SMTPConnectError, SMTPServerDisconnected, AWSConnectionError)

# Errors that involve exceeding a quota of sent email
QUOTA_EXCEEDED_ERRORS = (SESDailyQuotaExceededError, )

# Errors that mail is being sent too quickly. When caught by a task, it
# triggers an exponential backoff and retry. Retries happen continuously until
# the email is sent.
SENDING_RATE_ERRORS = (SESMaxSendingRateExceededError, )


def _get_recipient_queryset(user_id, to_option, course_id, course_location):
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
            enrollment_qset = User.objects.filter(
                courseenrollment__course_id=course_id,
                courseenrollment__is_active=True
            )
            recipient_qset = recipient_qset | enrollment_qset
        recipient_qset = recipient_qset.distinct()
    else:
        log.error("Unexpected bulk email TO_OPTION found: %s", to_option)
        raise Exception("Unexpected bulk email TO_OPTION found: {0}".format(to_option))
    recipient_qset = recipient_qset.order_by('pk')
    return recipient_qset


def _get_course_email_context(course):
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

    global_email_context = _get_course_email_context(course)
    recipient_qset = _get_recipient_queryset(user_id, to_option, course_id, course.location)
    total_num_emails = recipient_qset.count()

    log.info("Preparing to queue emails to %d recipient(s) for course %s, email %s, to_option %s",
             total_num_emails, course_id, email_id, to_option)

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
            if i == num_tasks_this_query - 1:
                # Avoid cutting off the very last email when chunking a task that divides perfectly
                # (eg num_emails_this_query = 297 and EMAILS_PER_TASK is 100)
                to_list = recipient_sublist[i * chunk:]
            else:
                to_list = recipient_sublist[i * chunk:i * chunk + chunk]
            subtask_id = str(uuid4())
            subtask_id_list.append(subtask_id)
            task_list.append(send_course_email.subtask((
                entry_id,
                email_id,
                to_list,
                global_email_context,
            ),
            task_id=subtask_id,
            routing_key=settings.HIGH_PRIORITY_QUEUE,
            ))
        num_workers += num_tasks_this_query

    # Update the InstructorTask  with information about the subtasks we've defined.
    progress = update_instructor_task_for_subtasks(entry, action_name, total_num_emails, subtask_id_list)
    num_subtasks = len(subtask_id_list)
    log.info("Preparing to queue %d email tasks for course %s, email %s, to %s",
             num_subtasks, course_id, email_id, to_option)

    # now group the subtasks, and start them running:
    task_group = group(task_list)
    task_group.apply_async(routing_key=settings.HIGH_PRIORITY_QUEUE)

    # We want to return progress here, as this is what will be stored in the
    # AsyncResult for the parent task as its return value.
    # The AsyncResult will then be marked as SUCCEEDED, and have this return value as it's "result".
    # That's okay, for the InstructorTask will have the "real" status, and monitoring code
    # will use that instead.
    return progress


# TODO: figure out if we really need this after all (for unit tests...)
def _get_current_task():
    """Stub to make it easier to test without actually running Celery"""
    return current_task


@task(default_retry_delay=15, max_retries=5)  # pylint: disable=E1102
def send_course_email(entry_id, email_id, to_list, global_email_context):
    """
    Sends an email to a list of recipients.

    Inputs are:
      * `entry_id`: id of the InstructorTask object to which progress should be recorded.
      * `email_id`: id of the CourseEmail model that is to be emailed.
      * `to_list`: list of recipients.  Each is represented as a dict with the following keys:
        - 'profile__name': full name of User.
        - 'email': email address of User.
        - 'pk': primary key of User model.
      * `global_email_context`: dict containing values to be used to fill in slots in email
        template.  It does not include 'name' and 'email', which will be provided by the to_list.
      * retry_index: counter indicating how many times this task has been retried.  Set to zero
        on initial call.

    Sends to all addresses contained in to_list that are not also in the Optout table.
    Emails are sent multi-part, in both plain text and html.  Updates InstructorTask object
    with status information (sends, failures, skips) and updates number of subtasks completed.
    """
    # Get entry here, as a sanity check that it actually exists.  We won't actually do anything
    # with it right away, but we also don't expect it to fail.
    InstructorTask.objects.get(pk=entry_id)

    # Get information from current task's request:
    current_task_id = _get_current_task().request.id
    num_to_send = len(to_list)
    log.info("Preparing to send %s emails as subtask %s for instructor task %d: request = %s",
             num_to_send, current_task_id, entry_id, _get_current_task().request)

    send_exception = None
    course_email_result_value = None
    try:
        course_title = global_email_context['course_title']
        with dog_stats_api.timer('course_email.single_task.time.overall', tags=[_statsd_tag(course_title)]):
            course_email_result_value, send_exception = _send_course_email(
                entry_id,
                email_id,
                to_list,
                global_email_context,
            )
    except Exception:
        # Unexpected exception. Try to write out the failure to the entry before failing
        _, send_exception, traceback = exc_info()
        traceback_string = format_exc(traceback) if traceback is not None else ''
        log.error("background task (%s) failed unexpectedly: %s %s", current_task_id, send_exception, traceback_string)
        # We got here for really unexpected reasons.  Since we don't know how far
        # the task got in emailing, we count all recipients as having failed.
        # It at least keeps the counts consistent.
        course_email_result_value = create_subtask_result(0, num_to_send, 0)

    if send_exception is None:
        # Update the InstructorTask object that is storing its progress.
        log.info("background task (%s) succeeded", current_task_id)
        update_subtask_status(entry_id, current_task_id, SUCCESS, course_email_result_value)
    elif isinstance(send_exception, RetryTaskError):
        # If retrying, record the progress made before the retry condition
        # was encountered.  Once the retry is running, it will be only processing
        # what wasn't already accomplished.
        log.warning("background task (%s) being retried", current_task_id)
        update_subtask_status(entry_id, current_task_id, RETRY, course_email_result_value)
        raise send_exception
    else:
        log.error("background task (%s) failed: %s", current_task_id, send_exception)
        update_subtask_status(entry_id, current_task_id, FAILURE, course_email_result_value)
        raise send_exception

    return course_email_result_value


def _send_course_email(entry_id, email_id, to_list, global_email_context):
    """
    Performs the email sending task.

    Sends an email to a list of recipients.

    Inputs are:
      * `entry_id`: id of the InstructorTask object to which progress should be recorded.
      * `email_id`: id of the CourseEmail model that is to be emailed.
      * `to_list`: list of recipients.  Each is represented as a dict with the following keys:
        - 'profile__name': full name of User.
        - 'email': email address of User.
        - 'pk': primary key of User model.
      * `global_email_context`: dict containing values to be used to fill in slots in email
        template.  It does not include 'name' and 'email', which will be provided by the to_list.

    Sends to all addresses contained in to_list that are not also in the Optout table.
    Emails are sent multi-part, in both plain text and html.

    Returns a tuple of two values:
      * First value is a dict which represents current progress.  Keys are:

        'attempted': number of emails attempted
        'succeeded': number of emails succeeded
        'skipped': number of emails skipped (due to optout)
        'failed': number of emails not sent because of some failure

      * Second value is an exception returned by the innards of the method, indicating a fatal error.
        In this case, the number of recipients that were not sent have already been added to the
        'failed' count above.
    """
    # Get information from current task's request:
    task_id = _get_current_task().request.id
    retry_index = _get_current_task().request.retries
    throttle = retry_index > 0

    num_optout = 0
    num_sent = 0
    num_error = 0

    try:
        course_email = CourseEmail.objects.get(id=email_id)
    except CourseEmail.DoesNotExist as exc:
        log.exception("Task %s: could not find email id:%s to send.", task_id, email_id)
        raise

    # Exclude optouts (if not a retry):
    # Note that we don't have to do the optout logic at all if this is a retry,
    # because we have presumably already performed the optout logic on the first
    # attempt.  Anyone on the to_list on a retry has already passed the filter
    # that existed at that time, and we don't need to keep checking for changes
    # in the Optout list.
    if retry_index == 0:
        optouts = (Optout.objects.filter(course_id=course_email.course_id,
                                         user__in=[i['pk'] for i in to_list])
                                 .values_list('user__email', flat=True))

        optouts = set(optouts)
        # Only count the num_optout for the first time the optouts are calculated.
        # We assume that the number will not change on retries, and so we don't need
        # to calculate it each time.
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

        # Define context values to use in all course emails:
        email_context = {
            'name': '',
            'email': ''
        }
        email_context.update(global_email_context)

        while to_list:
            # Update context with user-specific values from the user at the end of the list:
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
            if throttle:
                sleep(0.2)

            try:
                log.info('Email with id %s to be sent to %s', email_id, email)

                with dog_stats_api.timer('course_email.single_send.time.overall', tags=[_statsd_tag(course_title)]):
                    connection.send_messages([email_msg])

                dog_stats_api.increment('course_email.sent', tags=[_statsd_tag(course_title)])

                log.info('Email with id %s sent to %s', email_id, email)
                num_sent += 1
            except SMTPDataError as exc:
                # According to SMTP spec, we'll retry error codes in the 4xx range.  5xx range indicates hard failure.
                if exc.smtp_code >= 400 and exc.smtp_code < 500:
                    # This will cause the outer handler to catch the exception and retry the entire task
                    raise exc
                else:
                    # This will fall through and not retry the message, since it will be popped
                    log.warning('Task %s: email with id %s not delivered to %s due to error %s', task_id, email_id, email, exc.smtp_error)
                    dog_stats_api.increment('course_email.error', tags=[_statsd_tag(course_title)])
                    num_error += 1

            # Pop the user that was emailed off the end of the list:
            to_list.pop()

    except SENDING_RATE_ERRORS as exc:
        subtask_progress = create_subtask_result(num_sent, num_error, num_optout)
        return _submit_for_retry(
            entry_id, email_id, to_list, global_email_context, exc, subtask_progress, True
        )

    except RETRY_ERRORS as exc:
        # Errors caught here cause the email to be retried.  The entire task is actually retried
        # without popping the current recipient off of the existing list.
        # Errors caught are those that indicate a temporary condition that might succeed on retry.
        subtask_progress = create_subtask_result(num_sent, num_error, num_optout)
        return _submit_for_retry(
            entry_id, email_id, to_list, global_email_context, exc, subtask_progress, False
        )

    except Exception as exc:

        # If we have a general exception for this request, we need to figure out what to do with it.
        # If we're going to just mark it as failed
        # And the log message below should indicate which task_id is failing, so we have a chance to
        # reconstruct the problems.
        if isinstance(exc, QUOTA_EXCEEDED_ERRORS):
            log.exception('WARNING: Course "%s" exceeded quota!', course_title)
            log.exception('Email with id %d not sent due to exceeding quota. To list: %s',
                          email_id,
                          [i['email'] for i in to_list])
        else:
            log.exception('Task %s: email with id %d caused send_course_email task to fail with uncaught exception. To list: %s',
                          task_id, email_id, [i['email'] for i in to_list])
        num_error += len(to_list)
        return create_subtask_result(num_sent, num_error, num_optout), exc
    else:
        # Successful completion is marked by an exception value of None:
        return create_subtask_result(num_sent, num_error, num_optout), None
    finally:
        # clean up at the end
        connection.close()


def _submit_for_retry(entry_id, email_id, to_list, global_email_context, current_exception, subtask_progress, is_sending_rate_error):
    """
    Helper function to requeue a task for retry, using the new version of arguments provided.

    Inputs are the same as for running a task, plus two extra indicating the state at the time of retry.
    These include the `current_exception` that the task encountered that is causing the retry attempt,
    and the `subtask_progress` that is to be returned.

    Returns a tuple of two values:
      * First value is a dict which represents current progress.  Keys are:

        'attempted': number of emails attempted
        'succeeded': number of emails succeeded
        'skipped': number of emails skipped (due to optout)
        'failed': number of emails not sent because of some failure

      * Second value is an exception returned by the innards of the method.  If the retry was
        successfully submitted, this value will be the RetryTaskError that retry() returns.
        Otherwise, it (ought to be) the current_exception passed in.
    """
    task_id = _get_current_task().request.id
    retry_index = _get_current_task().request.retries

    log.warning('Task %s: email with id %d not delivered due to temporary error %s, retrying send to %d recipients',
                task_id, email_id, current_exception, len(to_list))

    # Don't resend emails that have already succeeded.
    # Retry the email at increasing exponential backoff.

    if is_sending_rate_error:
        countdown = ((2 ** retry_index) * 15) * random.uniform(.5, 1.5)
    else:
        countdown = ((2 ** retry_index) * 15) * random.uniform(.75, 1.5)

    try:
        send_course_email.retry(
            args=[
                entry_id,
                email_id,
                to_list,
                global_email_context,
            ],
            exc=current_exception,
            countdown=countdown,
            throw=True,
        )
    except RetryTaskError as retry_error:
        # If retry call is successful, update with the current progress:
        log.exception('Task %s: email with id %d caused send_course_email task to retry.',
                      task_id, email_id)
        return subtask_progress, retry_error
    except Exception as retry_exc:
        # If there are no more retries, because the maximum has been reached,
        # we expect the original exception to be raised.  We catch it here
        # (and put it in retry_exc just in case it's different, but it shouldn't be),
        # and update status as if it were any other failure.  That means that
        # the recipients still in the to_list are counted as failures.
        log.exception('Task %s: email with id %d caused send_course_email task to fail to retry. To list: %s',
                      task_id, email_id, [i['email'] for i in to_list])
        num_failed = len(to_list)
        new_subtask_progress = increment_subtask_result(subtask_progress, 0, num_failed, 0)
        return new_subtask_progress, retry_exc


def _statsd_tag(course_title):
    """
    Calculate the tag we will use for DataDog.
    """
    tag = "course_email:{0}".format(course_title)
    return tag[:200]
