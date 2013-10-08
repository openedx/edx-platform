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
from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError, SMTPException
from boto.ses.exceptions import (
    SESDailyQuotaExceededError,
    SESMaxSendingRateExceededError,
    SESAddressBlacklistedError,
    SESIllegalAddressError,
    SESLocalAddressCharacterError,
)
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
    create_subtask_status,
    increment_subtask_status,
    update_instructor_task_for_subtasks,
)

log = get_task_logger(__name__)


# Errors that an individual email is failing to be sent, and should just
# be treated as a fail.
SINGLE_EMAIL_FAILURE_ERRORS = (SESAddressBlacklistedError, SESIllegalAddressError, SESLocalAddressCharacterError)

# Exceptions that, if caught, should cause the task to be re-tried.
# These errors will be caught a limited number of times before the task fails.
LIMITED_RETRY_ERRORS = (SMTPConnectError, SMTPServerDisconnected, AWSConnectionError)

# Errors that indicate that a mailing task should be retried without limit.
# An example is if email is being sent too quickly, but may succeed if sent
# more slowly.  When caught by a task, it triggers an exponential backoff and retry.
# Retries happen continuously until the email is sent.
# Note that the SMTPDataErrors here are only those within the 4xx range.
# Those not in this range (i.e. in the 5xx range) are treated as hard failures
# and thus like SINGLE_EMAIL_FAILURE_ERRORS.
INFINITE_RETRY_ERRORS = (SESMaxSendingRateExceededError, SMTPDataError)

# Errors that are known to indicate an inability to send any more emails,
# and should therefore not be retried.  For example, exceeding a quota for emails.
# Also, any SMTP errors that are not explicitly enumerated above.
BULK_EMAIL_FAILURE_ERRORS = (SESDailyQuotaExceededError, SMTPException)


def _get_recipient_queryset(user_id, to_option, course_id, course_location):
    """
    Returns a query set of email recipients corresponding to the requested to_option category.

    `to_option` is either SEND_TO_MYSELF, SEND_TO_STAFF, or SEND_TO_ALL.

    Recipients who are in more than one category (e.g. enrolled in the course and are staff or self)
    will be properly deduped.
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
            # We also require students to have activated their accounts to
            # provide verification that the provided email address is valid.
            enrollment_qset = User.objects.filter(
                is_active=True,
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
    # Get inputs to use in this task from the entry.
    user_id = entry.requester.id
    task_id = entry.task_id

    # Perfunctory check, since expansion is made for convenience of other task
    # code that doesn't need the entry_id.
    if course_id != entry.course_id:
        format_msg = "Course id conflict: explicit value %s does not match task value %s"
        raise ValueError(format_msg.format(course_id, entry.course_id))

    email_id = task_input['email_id']
    try:
        email_obj = CourseEmail.objects.get(id=email_id)
    except CourseEmail.DoesNotExist as exc:
        # The CourseEmail object should be committed in the view function before the task
        # is submitted and reaches this point.
        log.warning("Task %s: Failed to get CourseEmail with id %s", task_id, email_id)
        raise

    to_option = email_obj.to_option

    # Sanity check that course for email_obj matches that of the task referencing it.
    if course_id != email_obj.course_id:
        format_msg = "Course id conflict: explicit value %s does not match email value %s"
        raise ValueError(format_msg.format(course_id, email_obj.course_id))

    try:
        course = get_course_by_id(course_id, depth=1)
    except Http404 as exc:
        log.exception("Task %s: get_course_by_id failed: %s", task_id, exc.args[0])
        raise ValueError("Course not found: " + exc.args[0])

    global_email_context = _get_course_email_context(course)
    recipient_qset = _get_recipient_queryset(user_id, to_option, course_id, course.location)
    total_num_emails = recipient_qset.count()

    log.info("Task %s: Preparing to queue emails to %d recipient(s) for course %s, email %s, to_option %s",
             task_id, total_num_emails, course_id, email_id, to_option)

    num_queries = int(math.ceil(float(total_num_emails) / float(settings.EMAILS_PER_QUERY)))
    last_pk = recipient_qset[0].pk - 1
    num_emails_queued = 0
    task_list = []
    subtask_id_list = []
    for _ in range(num_queries):
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
            subtask_status = create_subtask_status(subtask_id)
            # Create subtask, passing args and kwargs.
            # This includes specifying the task_id to use, so we can track it.
            # Specify the routing key as part of it, which is used by
            # Celery to route the task request to the right worker.
            new_subtask = send_course_email.subtask(
                (
                    entry_id,
                    email_id,
                    to_list,
                    global_email_context,
                    subtask_status,
                ),
                task_id=subtask_id,
                routing_key=settings.BULK_EMAIL_ROUTING_KEY,
            )
            task_list.append(new_subtask)
        num_emails_queued += num_emails_this_query

    # Sanity check: we expect the chunking to be properly summing to the original count:
    if num_emails_queued != total_num_emails:
        error_msg = "Task {}: number of emails generated by chunking {} not equal to original total {}".format(
            task_id, num_emails_queued, total_num_emails
        )
        log.error(error_msg)
        raise Exception(error_msg)

    # Update the InstructorTask  with information about the subtasks we've defined.
    progress = update_instructor_task_for_subtasks(entry, action_name, total_num_emails, subtask_id_list)
    num_subtasks = len(subtask_id_list)
    log.info("Preparing to queue %d email tasks (%d emails) for course %s, email %s, to %s",
             num_subtasks, total_num_emails, course_id, email_id, to_option)

    # Now group the subtasks, and start them running.  This allows all the subtasks
    # in the list to be submitted at the same time.
    task_group = group(task_list)
    task_group.apply_async(routing_key=settings.BULK_EMAIL_ROUTING_KEY)

    # We want to return progress here, as this is what will be stored in the
    # AsyncResult for the parent task as its return value.
    # The AsyncResult will then be marked as SUCCEEDED, and have this return value as its "result".
    # That's okay, for the InstructorTask will have the "real" status, and monitoring code
    # should be using that instead.
    return progress


@task(default_retry_delay=settings.BULK_EMAIL_DEFAULT_RETRY_DELAY, max_retries=settings.BULK_EMAIL_MAX_RETRIES)  # pylint: disable=E1102
def send_course_email(entry_id, email_id, to_list, global_email_context, subtask_status):
    """
    Sends an email to a list of recipients.

    Inputs are:
      * `entry_id`: id of the InstructorTask object to which progress should be recorded.
      * `email_id`: id of the CourseEmail model that is to be emailed.
      * `to_list`: list of recipients.  Each is represented as a dict with the following keys:
        - 'profile__name': full name of User.
        - 'email': email address of User.
        - 'pk': primary key of User model.
      * `global_email_context`: dict containing values that are unique for this email but the same
        for all recipients of this email.  This dict is to be used to fill in slots in email
        template.  It does not include 'name' and 'email', which will be provided by the to_list.
      * `subtask_status` : dict containing values representing current status.  Keys are:

        'task_id' : id of subtask.  This is used to pass task information across retries.
        'attempted' : number of attempts -- should equal succeeded plus failed
        'succeeded' : number that succeeded in processing
        'skipped' : number that were not processed.
        'failed' : number that failed during processing
        'retried_nomax' : number of times the subtask has been retried for conditions that
            should not have a maximum count applied
        'retried_withmax' : number of times the subtask has been retried for conditions that
            should have a maximum count applied
        'state' : celery state of the subtask (e.g. QUEUING, PROGRESS, RETRY, FAILURE, SUCCESS)

        Most values will be zero on initial call, but may be different when the task is
        invoked as part of a retry.

    Sends to all addresses contained in to_list that are not also in the Optout table.
    Emails are sent multi-part, in both plain text and html.  Updates InstructorTask object
    with status information (sends, failures, skips) and updates number of subtasks completed.
    """
    # Get entry here, as a sanity check that it actually exists.  We won't actually do anything
    # with it right away, but we also don't expect it to fail.
    InstructorTask.objects.get(pk=entry_id)

    current_task_id = subtask_status['task_id']
    num_to_send = len(to_list)
    log.info("Preparing to send email %s to %d recipients as subtask %s for instructor task %d: context = %s, status=%s",
             email_id, num_to_send, current_task_id, entry_id, global_email_context, subtask_status)

    send_exception = None
    new_subtask_status = None
    try:
        course_title = global_email_context['course_title']
        with dog_stats_api.timer('course_email.single_task.time.overall', tags=[_statsd_tag(course_title)]):
            new_subtask_status, send_exception = _send_course_email(
                entry_id,
                email_id,
                to_list,
                global_email_context,
                subtask_status,
            )
    except Exception:
        # Unexpected exception. Try to write out the failure to the entry before failing.
        _, send_exception, traceback = exc_info()
        traceback_string = format_exc(traceback) if traceback is not None else ''
        log.error("Send-email task %s: failed unexpectedly: %s %s", current_task_id, send_exception, traceback_string)
        # We got here for really unexpected reasons.  Since we don't know how far
        # the task got in emailing, we count all recipients as having failed.
        # It at least keeps the counts consistent.
        new_subtask_status = increment_subtask_status(subtask_status, failed=num_to_send, state=FAILURE)
        update_subtask_status(entry_id, current_task_id, new_subtask_status)
        raise send_exception

    if send_exception is None:
        # Update the InstructorTask object that is storing its progress.
        log.info("Send-email task %s: succeeded", current_task_id)
        update_subtask_status(entry_id, current_task_id, new_subtask_status)
    elif isinstance(send_exception, RetryTaskError):
        # If retrying, record the progress made before the retry condition
        # was encountered.  Once the retry is running, it will be only processing
        # what wasn't already accomplished.
        log.warning("Send-email task %s: being retried", current_task_id)
        update_subtask_status(entry_id, current_task_id, new_subtask_status)
        raise send_exception
    else:
        log.error("Send-email task %s: failed: %s", current_task_id, send_exception)
        update_subtask_status(entry_id, current_task_id, new_subtask_status)
        raise send_exception

    log.info("Send-email task %s: returning status %s", current_task_id, new_subtask_status)
    return new_subtask_status


def _send_course_email(entry_id, email_id, to_list, global_email_context, subtask_status):
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
      * `global_email_context`: dict containing values that are unique for this email but the same
        for all recipients of this email.  This dict is to be used to fill in slots in email
        template.  It does not include 'name' and 'email', which will be provided by the to_list.
      * `subtask_status` : dict containing values representing current status.  Keys are:

        'task_id' : id of subtask.  This is used to pass task information across retries.
        'attempted' : number of attempts -- should equal succeeded plus failed
        'succeeded' : number that succeeded in processing
        'skipped' : number that were not processed.
        'failed' : number that failed during processing
        'retried_nomax' : number of times the subtask has been retried for conditions that
            should not have a maximum count applied
        'retried_withmax' : number of times the subtask has been retried for conditions that
            should have a maximum count applied
        'state' : celery state of the subtask (e.g. QUEUING, PROGRESS, RETRY, FAILURE, SUCCESS)

    Sends to all addresses contained in to_list that are not also in the Optout table.
    Emails are sent multi-part, in both plain text and html.

    Returns a tuple of two values:
      * First value is a dict which represents current progress at the end of this call.  Keys are
        the same as for the input subtask_status.

      * Second value is an exception returned by the innards of the method, indicating a fatal error.
        In this case, the number of recipients that were not sent have already been added to the
        'failed' count above.
    """
    # Get information from current task's request:
    task_id = subtask_status['task_id']

    # If this is a second attempt due to rate-limits, then throttle the speed at which mail is sent:
    throttle = subtask_status['retried_nomax'] > 0

    # collect stats on progress:
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
    if (subtask_status['retried_nomax'] + subtask_status['retried_withmax']) == 0:
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

            # Throttle if we have gotten the rate limiter
            if throttle:
                sleep(0.2)

            try:
                log.debug('Email with id %s to be sent to %s', email_id, email)

                with dog_stats_api.timer('course_email.single_send.time.overall', tags=[_statsd_tag(course_title)]):
                    connection.send_messages([email_msg])

            except SMTPDataError as exc:
                # According to SMTP spec, we'll retry error codes in the 4xx range.  5xx range indicates hard failure.
                if exc.smtp_code >= 400 and exc.smtp_code < 500:
                    # This will cause the outer handler to catch the exception and retry the entire task.
                    raise exc
                else:
                    # This will fall through and not retry the message.
                    log.warning('Task %s: email with id %s not delivered to %s due to error %s', task_id, email_id, email, exc.smtp_error)
                    dog_stats_api.increment('course_email.error', tags=[_statsd_tag(course_title)])
                    num_error += 1

            except SINGLE_EMAIL_FAILURE_ERRORS as exc:
                # This will fall through and not retry the message.
                log.warning('Task %s: email with id %s not delivered to %s due to error %s', task_id, email_id, email, exc)
                dog_stats_api.increment('course_email.error', tags=[_statsd_tag(course_title)])
                num_error += 1

            else:
                dog_stats_api.increment('course_email.sent', tags=[_statsd_tag(course_title)])
                if settings.BULK_EMAIL_LOG_SENT_EMAILS:
                    log.info('Email with id %s sent to %s', email_id, email)
                else:
                    log.debug('Email with id %s sent to %s', email_id, email)
                num_sent += 1

            # Pop the user that was emailed off the end of the list:
            to_list.pop()

    except INFINITE_RETRY_ERRORS as exc:
        dog_stats_api.increment('course_email.infinite_retry', tags=[_statsd_tag(course_title)])
        # Increment the "retried_nomax" counter, update other counters with progress to date,
        # and set the state to RETRY:
        subtask_progress = increment_subtask_status(
            subtask_status,
            succeeded=num_sent,
            failed=num_error,
            skipped=num_optout,
            retried_nomax=1,
            state=RETRY
        )
        return _submit_for_retry(
            entry_id, email_id, to_list, global_email_context, exc, subtask_progress, skip_retry_max=True
        )

    except LIMITED_RETRY_ERRORS as exc:
        # Errors caught here cause the email to be retried.  The entire task is actually retried
        # without popping the current recipient off of the existing list.
        # Errors caught are those that indicate a temporary condition that might succeed on retry.
        dog_stats_api.increment('course_email.limited_retry', tags=[_statsd_tag(course_title)])
        # Increment the "retried_withmax" counter, update other counters with progress to date,
        # and set the state to RETRY:
        subtask_progress = increment_subtask_status(
            subtask_status,
            succeeded=num_sent,
            failed=num_error,
            skipped=num_optout,
            retried_withmax=1,
            state=RETRY
        )
        return _submit_for_retry(
            entry_id, email_id, to_list, global_email_context, exc, subtask_progress, skip_retry_max=False
        )

    except BULK_EMAIL_FAILURE_ERRORS as exc:
        dog_stats_api.increment('course_email.error', tags=[_statsd_tag(course_title)])
        num_pending = len(to_list)
        log.exception('Task %s: email with id %d caused send_course_email task to fail with "fatal" exception.  %d emails unsent.',
                      task_id, email_id, num_pending)
        # Update counters with progress to date, counting unsent emails as failures,
        # and set the state to FAILURE:
        subtask_progress = increment_subtask_status(
            subtask_status,
            succeeded=num_sent,
            failed=(num_error + num_pending),
            skipped=num_optout,
            state=FAILURE
        )
        return subtask_progress, exc

    except Exception as exc:
        # Errors caught here cause the email to be retried.  The entire task is actually retried
        # without popping the current recipient off of the existing list.
        # These are unexpected errors.  Since they might be due to a temporary condition that might
        # succeed on retry, we give them a retry.
        dog_stats_api.increment('course_email.limited_retry', tags=[_statsd_tag(course_title)])
        log.exception('Task %s: email with id %d caused send_course_email task to fail with unexpected exception.  Generating retry.',
                      task_id, email_id)
        # Increment the "retried_withmax" counter, update other counters with progress to date,
        # and set the state to RETRY:
        subtask_progress = increment_subtask_status(
            subtask_status,
            succeeded=num_sent,
            failed=num_error,
            skipped=num_optout,
            retried_withmax=1,
            state=RETRY
        )
        return _submit_for_retry(
            entry_id, email_id, to_list, global_email_context, exc, subtask_progress, skip_retry_max=False
        )

    else:
        # All went well.  Update counters with progress to date,
        # and set the state to SUCCESS:
        subtask_progress = increment_subtask_status(
            subtask_status,
            succeeded=num_sent,
            failed=num_error,
            skipped=num_optout,
            state=SUCCESS
        )
        # Successful completion is marked by an exception value of None.
        return subtask_progress, None
    finally:
        # Clean up at the end.
        connection.close()


def _get_current_task():
    """
    Stub to make it easier to test without actually running Celery.

    This is a wrapper around celery.current_task, which provides access
    to the top of the stack of Celery's tasks.  When running tests, however,
    it doesn't seem to work to mock current_task directly, so this wrapper
    is used to provide a hook to mock in tests, while providing the real
    `current_task` in production.
    """
    return current_task


def _submit_for_retry(entry_id, email_id, to_list, global_email_context, current_exception, subtask_status, skip_retry_max=False):
    """
    Helper function to requeue a task for retry, using the new version of arguments provided.

    Inputs are the same as for running a task, plus two extra indicating the state at the time of retry.
    These include the `current_exception` that the task encountered that is causing the retry attempt,
    and the `subtask_status` that is to be returned.  A third extra argument `skip_retry_max`
    indicates whether the current retry should be subject to a maximum test.

    Returns a tuple of two values:
      * First value is a dict which represents current progress.  Keys are:

        'task_id' : id of subtask.  This is used to pass task information across retries.
        'attempted' : number of attempts -- should equal succeeded plus failed
        'succeeded' : number that succeeded in processing
        'skipped' : number that were not processed.
        'failed' : number that failed during processing
        'retried_nomax' : number of times the subtask has been retried for conditions that
            should not have a maximum count applied
        'retried_withmax' : number of times the subtask has been retried for conditions that
            should have a maximum count applied
        'state' : celery state of the subtask (e.g. QUEUING, PROGRESS, RETRY, FAILURE, SUCCESS)

      * Second value is an exception returned by the innards of the method.  If the retry was
        successfully submitted, this value will be the RetryTaskError that retry() returns.
        Otherwise, it (ought to be) the current_exception passed in.
    """
    task_id = subtask_status['task_id']
    log.info("Task %s: Successfully sent to %s users; failed to send to %s users (and skipped %s users)",
             task_id, subtask_status['succeeded'], subtask_status['failed'], subtask_status['skipped'])

    # Calculate time until we retry this task (in seconds):
    # The value for max_retries is increased by the number of times an "infinite-retry" exception
    # has been retried.  We want the regular retries to trigger max-retry checking, but not these
    # special retries.  So we count them separately.
    max_retries = _get_current_task().max_retries + subtask_status['retried_nomax']
    base_delay = _get_current_task().default_retry_delay
    if skip_retry_max:
        # once we reach five retries, don't increase the countdown further.
        retry_index = min(subtask_status['retried_nomax'], 5)
        exception_type = 'sending-rate'
    else:
        retry_index = subtask_status['retried_withmax']
        exception_type = 'transient'

    # Skew the new countdown value by a random factor, so that not all
    # retries are deferred by the same amount.
    countdown = ((2 ** retry_index) * base_delay) * random.uniform(.75, 1.25)

    log.warning('Task %s: email with id %d not delivered due to %s error %s, retrying send to %d recipients in %s seconds (with max_retry=%s)',
                task_id, email_id, exception_type, current_exception, len(to_list), countdown, max_retries)

    try:
        send_course_email.retry(
            args=[
                entry_id,
                email_id,
                to_list,
                global_email_context,
                subtask_status,
            ],
            exc=current_exception,
            countdown=countdown,
            max_retries=max_retries,
            throw=True,
        )
    except RetryTaskError as retry_error:
        # If the retry call is successful, update with the current progress:
        log.exception('Task %s: email with id %d caused send_course_email task to retry.',
                      task_id, email_id)
        return subtask_status, retry_error
    except Exception as retry_exc:
        # If there are no more retries, because the maximum has been reached,
        # we expect the original exception to be raised.  We catch it here
        # (and put it in retry_exc just in case it's different, but it shouldn't be),
        # and update status as if it were any other failure.  That means that
        # the recipients still in the to_list are counted as failures.
        log.exception('Task %s: email with id %d caused send_course_email task to fail to retry. To list: %s',
                      task_id, email_id, [i['email'] for i in to_list])
        num_failed = len(to_list)
        new_subtask_progress = increment_subtask_status(subtask_status, failed=num_failed, state=FAILURE)
        return new_subtask_progress, retry_exc


def _statsd_tag(course_title):
    """
    Calculate the tag we will use for DataDog.
    """
    tag = "course_email:{0}".format(course_title)
    return tag[:200]
