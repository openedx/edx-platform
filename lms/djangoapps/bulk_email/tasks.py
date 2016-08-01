# -*- coding: utf-8 -*-
"""
This module contains celery task functions for handling the sending of bulk email
to a course.
"""
from collections import Counter
import json
import logging
import random
import re
from time import sleep

import dogstats_wrapper as dog_stats_api
from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError, SMTPException
from boto.ses.exceptions import (
    SESAddressNotVerifiedError,
    SESIdentityNotVerifiedError,
    SESDomainNotConfirmedError,
    SESAddressBlacklistedError,
    SESDailyQuotaExceededError,
    SESMaxSendingRateExceededError,
    SESDomainEndsWithDotError,
    SESLocalAddressCharacterError,
    SESIllegalAddressError,
)
from boto.exception import AWSConnectionError
from markupsafe import escape

from celery import task, current_task  # pylint: disable=no-name-in-module
from celery.states import SUCCESS, FAILURE, RETRY  # pylint: disable=no-name-in-module, import-error
from celery.exceptions import RetryTaskError  # pylint: disable=no-name-in-module, import-error

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.message import forbid_multi_line_headers
from django.core.urlresolvers import reverse

from bulk_email.models import (
    CourseEmail, Optout, Target
)
from courseware.courses import get_course
from openedx.core.lib.courses import course_image_url
from student.roles import CourseStaffRole, CourseInstructorRole
from instructor_task.models import InstructorTask
from instructor_task.subtasks import (
    SubtaskStatus,
    queue_subtasks_for_query,
    check_subtask_is_valid,
    update_subtask_status,
)
from util.query import use_read_replica_if_available
from util.date_utils import get_default_time_display
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger('edx.celery.task')


# Errors that an individual email is failing to be sent, and should just
# be treated as a fail.
SINGLE_EMAIL_FAILURE_ERRORS = (
    SESAddressBlacklistedError,  # Recipient's email address has been temporarily blacklisted.
    SESDomainEndsWithDotError,  # Recipient's email address' domain ends with a period/dot.
    SESIllegalAddressError,  # Raised when an illegal address is encountered.
    SESLocalAddressCharacterError,  # An address contained a control or whitespace character.
)

# Exceptions that, if caught, should cause the task to be re-tried.
# These errors will be caught a limited number of times before the task fails.
LIMITED_RETRY_ERRORS = (
    SMTPConnectError,
    SMTPServerDisconnected,
    AWSConnectionError,
)

# Errors that indicate that a mailing task should be retried without limit.
# An example is if email is being sent too quickly, but may succeed if sent
# more slowly.  When caught by a task, it triggers an exponential backoff and retry.
# Retries happen continuously until the email is sent.
# Note that the SMTPDataErrors here are only those within the 4xx range.
# Those not in this range (i.e. in the 5xx range) are treated as hard failures
# and thus like SINGLE_EMAIL_FAILURE_ERRORS.
INFINITE_RETRY_ERRORS = (
    SESMaxSendingRateExceededError,  # Your account's requests/second limit has been exceeded.
    SMTPDataError,
)

# Errors that are known to indicate an inability to send any more emails,
# and should therefore not be retried.  For example, exceeding a quota for emails.
# Also, any SMTP errors that are not explicitly enumerated above.
BULK_EMAIL_FAILURE_ERRORS = (
    SESAddressNotVerifiedError,  # Raised when a "Reply-To" address has not been validated in SES yet.
    SESIdentityNotVerifiedError,  # Raised when an identity has not been verified in SES yet.
    SESDomainNotConfirmedError,  # Raised when domain ownership is not confirmed for DKIM.
    SESDailyQuotaExceededError,  # 24-hour allotment of outbound email has been exceeded.
    SMTPException,
)


def _get_course_email_context(course):
    """
    Returns context arguments to apply to all emails, independent of recipient.
    """
    course_id = course.id.to_deprecated_string()
    course_title = course.display_name
    course_end_date = get_default_time_display(course.end)
    course_url = '{}{}'.format(
        settings.LMS_ROOT_URL,
        reverse('course_root', kwargs={'course_id': course_id})
    )
    image_url = u'{}{}'.format(settings.LMS_ROOT_URL, course_image_url(course))
    email_context = {
        'course_title': course_title,
        'course_url': course_url,
        'course_image_url': image_url,
        'course_end_date': course_end_date,
        'account_settings_url': '{}{}'.format(settings.LMS_ROOT_URL, reverse('account_settings')),
        'email_settings_url': '{}{}'.format(settings.LMS_ROOT_URL, reverse('dashboard')),
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
    }
    return email_context


def perform_delegate_email_batches(entry_id, course_id, task_input, action_name):
    """
    Delegates emails by querying for the list of recipients who should
    get the mail, chopping up into batches of no more than settings.BULK_EMAIL_EMAILS_PER_TASK
    in size, and queueing up worker jobs.
    """
    entry = InstructorTask.objects.get(pk=entry_id)
    # Get inputs to use in this task from the entry.
    user_id = entry.requester.id
    task_id = entry.task_id

    # Perfunctory check, since expansion is made for convenience of other task
    # code that doesn't need the entry_id.
    if course_id != entry.course_id:
        format_msg = u"Course id conflict: explicit value %r does not match task value %r"
        log.warning(u"Task %s: " + format_msg, task_id, course_id, entry.course_id)
        raise ValueError(format_msg % (course_id, entry.course_id))

    # Fetch the CourseEmail.
    email_id = task_input['email_id']
    try:
        email_obj = CourseEmail.objects.get(id=email_id)
    except CourseEmail.DoesNotExist:
        # The CourseEmail object should be committed in the view function before the task
        # is submitted and reaches this point.
        log.warning(u"Task %s: Failed to get CourseEmail with id %s", task_id, email_id)
        raise

    # Check to see if email batches have already been defined.  This seems to
    # happen sometimes when there is a loss of connection while a task is being
    # queued.  When this happens, the same task gets called again, and a whole
    # new raft of subtasks gets queued up.  We will assume that if subtasks
    # have already been defined, there is no need to redefine them below.
    # So we just return right away.  We don't raise an exception, because we want
    # the current task to be marked with whatever it had been marked with before.
    if len(entry.subtasks) > 0 and len(entry.task_output) > 0:
        log.warning(u"Task %s has already been processed for email %s!  InstructorTask = %s", task_id, email_id, entry)
        progress = json.loads(entry.task_output)
        return progress

    # Sanity check that course for email_obj matches that of the task referencing it.
    if course_id != email_obj.course_id:
        format_msg = u"Course id conflict: explicit value %r does not match email value %r"
        log.warning(u"Task %s: " + format_msg, task_id, course_id, email_obj.course_id)
        raise ValueError(format_msg % (course_id, email_obj.course_id))

    # Fetch the course object.
    course = get_course(course_id)

    # Get arguments that will be passed to every subtask.
    targets = email_obj.targets.all()
    global_email_context = _get_course_email_context(course)

    recipient_qsets = [
        target.get_users(course_id, user_id)
        for target in targets
    ]
    combined_set = User.objects.none()
    for qset in recipient_qsets:
        combined_set |= qset
    combined_set = combined_set.distinct()
    recipient_fields = ['profile__name', 'email']

    log.info(u"Task %s: Preparing to queue subtasks for sending emails for course %s, email %s",
             task_id, course_id, email_id)

    total_recipients = combined_set.count()

    routing_key = settings.BULK_EMAIL_ROUTING_KEY
    # if there are few enough emails, send them through a different queue
    # to avoid large courses blocking emails to self and staff
    if total_recipients <= settings.BULK_EMAIL_JOB_SIZE_THRESHOLD:
        routing_key = settings.BULK_EMAIL_ROUTING_KEY_SMALL_JOBS

    # Weird things happen if we allow empty querysets as input to emailing subtasks
    # The task appears to hang at "0 out of 0 completed" and never finishes.
    if total_recipients == 0:
        msg = u"Bulk Email Task: Empty recipient set"
        log.warning(msg)
        raise ValueError(msg)

    def _create_send_email_subtask(to_list, initial_subtask_status):
        """Creates a subtask to send email to a given recipient list."""
        subtask_id = initial_subtask_status.task_id
        new_subtask = send_course_email.subtask(
            (
                entry_id,
                email_id,
                to_list,
                global_email_context,
                initial_subtask_status.to_dict(),
            ),
            task_id=subtask_id,
            routing_key=routing_key,
        )
        return new_subtask

    progress = queue_subtasks_for_query(
        entry,
        action_name,
        _create_send_email_subtask,
        [combined_set],
        recipient_fields,
        settings.BULK_EMAIL_EMAILS_PER_TASK,
        total_recipients,
    )

    # We want to return progress here, as this is what will be stored in the
    # AsyncResult for the parent task as its return value.
    # The AsyncResult will then be marked as SUCCEEDED, and have this return value as its "result".
    # That's okay, for the InstructorTask will have the "real" status, and monitoring code
    # should be using that instead.
    return progress


@task(default_retry_delay=settings.BULK_EMAIL_DEFAULT_RETRY_DELAY, max_retries=settings.BULK_EMAIL_MAX_RETRIES)
def send_course_email(entry_id, email_id, to_list, global_email_context, subtask_status_dict):
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
      * `subtask_status_dict` : dict containing values representing current status.  Keys are:

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
    subtask_status = SubtaskStatus.from_dict(subtask_status_dict)
    current_task_id = subtask_status.task_id
    num_to_send = len(to_list)
    log.info((u"Preparing to send email %s to %d recipients as subtask %s "
              u"for instructor task %d: context = %s, status=%s"),
             email_id, num_to_send, current_task_id, entry_id, global_email_context, subtask_status)

    # Check that the requested subtask is actually known to the current InstructorTask entry.
    # If this fails, it throws an exception, which should fail this subtask immediately.
    # This can happen when the parent task has been run twice, and results in duplicate
    # subtasks being created for the same InstructorTask entry.  This can happen when Celery
    # loses its connection to its broker, and any current tasks get requeued.
    # We hope to catch this condition in perform_delegate_email_batches() when it's the parent
    # task that is resubmitted, but just in case we fail to do so there, we check here as well.
    # There is also a possibility that this task will be run twice by Celery, for the same reason.
    # To deal with that, we need to confirm that the task has not already been completed.
    check_subtask_is_valid(entry_id, current_task_id, subtask_status)

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
        log.exception("Send-email task %s for email %s: failed unexpectedly!", current_task_id, email_id)
        # We got here for really unexpected reasons.  Since we don't know how far
        # the task got in emailing, we count all recipients as having failed.
        # It at least keeps the counts consistent.
        subtask_status.increment(failed=num_to_send, state=FAILURE)
        update_subtask_status(entry_id, current_task_id, subtask_status)
        raise

    if send_exception is None:
        # Update the InstructorTask object that is storing its progress.
        log.info("Send-email task %s for email %s: succeeded", current_task_id, email_id)
        update_subtask_status(entry_id, current_task_id, new_subtask_status)
    elif isinstance(send_exception, RetryTaskError):
        # If retrying, a RetryTaskError needs to be returned to Celery.
        # We assume that the the progress made before the retry condition
        # was encountered has already been updated before the retry call was made,
        # so we only log here.
        log.warning("Send-email task %s for email %s: being retried", current_task_id, email_id)
        raise send_exception  # pylint: disable=raising-bad-type
    else:
        log.error("Send-email task %s for email %s: failed: %s", current_task_id, email_id, send_exception)
        update_subtask_status(entry_id, current_task_id, new_subtask_status)
        raise send_exception  # pylint: disable=raising-bad-type

    # return status in a form that can be serialized by Celery into JSON:
    log.info("Send-email task %s for email %s: returning status %s", current_task_id, email_id, new_subtask_status)
    return new_subtask_status.to_dict()


def _filter_optouts_from_recipients(to_list, course_id):
    """
    Filters a recipient list based on student opt-outs for a given course.

    Returns the filtered recipient list, as well as the number of optouts
    removed from the list.
    """
    optouts = Optout.objects.filter(
        course_id=course_id,
        user__in=[i['pk'] for i in to_list]
    ).values_list('user__email', flat=True)
    optouts = set(optouts)
    # Only count the num_optout for the first time the optouts are calculated.
    # We assume that the number will not change on retries, and so we don't need
    # to calculate it each time.
    num_optout = len(optouts)
    to_list = [recipient for recipient in to_list if recipient['email'] not in optouts]
    return to_list, num_optout


def _get_source_address(course_id, course_title, truncate=True):
    """
    Calculates an email address to be used as the 'from-address' for sent emails.

    Makes a unique from name and address for each course, e.g.

        "COURSE_TITLE" Course Staff <course_name-no-reply@courseupdates.edx.org>

    If, when decoded to ascii, this from_addr is longer than 320 characters,
    use the course_name rather than the course title, e.g.

        "course_name" Course Staff <course_name-no-reply@courseupdates.edx.org>

    The "truncate" kwarg is only used for tests.

    """
    course_title_no_quotes = re.sub(r'"', '', course_title)

    # For the email address, get the course.  Then make sure that it can be used
    # in an email address, by substituting a '_' anywhere a non-(ascii, period, or dash)
    # character appears.
    course_name = re.sub(r"[^\w.-]", '_', course_id.course)

    from_addr_format = u'"{course_title}" Course Staff <{course_name}-{from_email}>'

    def format_address(course_title_no_quotes):
        """
        Partial function for formatting the from_addr. Since
        `course_title_no_quotes` may be truncated to make sure the returned
        string has fewer than 320 characters, we define this function to make
        it easy to determine quickly what the max length is for
        `course_title_no_quotes`.
        """
        return from_addr_format.format(
            course_title=course_title_no_quotes,
            course_name=course_name,
            from_email=configuration_helpers.get_value(
                'email_from_address',
                settings.BULK_EMAIL_DEFAULT_FROM_EMAIL
            )
        )

    from_addr = format_address(course_title_no_quotes)

    # If the encoded from_addr is longer than 320 characters, reformat,
    # but with the course name rather than course title.
    # Amazon SES's from address field appears to have a maximum length of 320.
    __, encoded_from_addr = forbid_multi_line_headers('from', from_addr, 'utf-8')

    # It seems that this value is also escaped when set out to amazon, judging
    # from our logs
    escaped_encoded_from_addr = escape(encoded_from_addr)
    if len(escaped_encoded_from_addr) >= 320 and truncate:
        from_addr = format_address(course_name)

    return from_addr


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
      * `subtask_status` : object of class SubtaskStatus representing current status.

    Sends to all addresses contained in to_list that are not also in the Optout table.
    Emails are sent multi-part, in both plain text and html.

    Returns a tuple of two values:
      * First value is a SubtaskStatus object which represents current progress at the end of this call.

      * Second value is an exception returned by the innards of the method, indicating a fatal error.
        In this case, the number of recipients that were not sent have already been added to the
        'failed' count above.
    """
    # Get information from current task's request:
    parent_task_id = InstructorTask.objects.get(pk=entry_id).task_id
    task_id = subtask_status.task_id
    total_recipients = len(to_list)
    recipient_num = 0
    total_recipients_successful = 0
    total_recipients_failed = 0
    recipients_info = Counter()

    log.info(
        "BulkEmail ==> Task: %s, SubTask: %s, EmailId: %s, TotalRecipients: %s",
        parent_task_id,
        task_id,
        email_id,
        total_recipients
    )

    try:
        course_email = CourseEmail.objects.get(id=email_id)
    except CourseEmail.DoesNotExist as exc:
        log.exception(
            "BulkEmail ==> Task: %s, SubTask: %s, EmailId: %s, Could not find email to send.",
            parent_task_id,
            task_id,
            email_id
        )
        raise

    # Exclude optouts (if not a retry):
    # Note that we don't have to do the optout logic at all if this is a retry,
    # because we have presumably already performed the optout logic on the first
    # attempt.  Anyone on the to_list on a retry has already passed the filter
    # that existed at that time, and we don't need to keep checking for changes
    # in the Optout list.
    if subtask_status.get_retry_count() == 0:
        to_list, num_optout = _filter_optouts_from_recipients(to_list, course_email.course_id)
        subtask_status.increment(skipped=num_optout)

    course_title = global_email_context['course_title']

    # use the email from address in the CourseEmail, if it is present, otherwise compute it
    from_addr = course_email.from_addr if course_email.from_addr else \
        _get_source_address(course_email.course_id, course_title)

    # use the CourseEmailTemplate that was associated with the CourseEmail
    course_email_template = course_email.get_template()
    try:
        connection = get_connection()
        connection.open()

        # Define context values to use in all course emails:
        email_context = {'name': '', 'email': ''}
        email_context.update(global_email_context)

        while to_list:
            # Update context with user-specific values from the user at the end of the list.
            # At the end of processing this user, they will be popped off of the to_list.
            # That way, the to_list will always contain the recipients remaining to be emailed.
            # This is convenient for retries, which will need to send to those who haven't
            # yet been emailed, but not send to those who have already been sent to.
            recipient_num += 1
            current_recipient = to_list[-1]
            email = current_recipient['email']
            email_context['email'] = email
            email_context['name'] = current_recipient['profile__name']
            email_context['user_id'] = current_recipient['pk']
            email_context['course_id'] = course_email.course_id

            # Construct message content using templates and context:
            plaintext_msg = course_email_template.render_plaintext(course_email.text_message, email_context)
            html_msg = course_email_template.render_htmltext(course_email.html_message, email_context)

            # Create email:
            email_msg = EmailMultiAlternatives(
                course_email.subject,
                plaintext_msg,
                from_addr,
                [email],
                connection=connection
            )
            email_msg.attach_alternative(html_msg, 'text/html')

            # Throttle if we have gotten the rate limiter.  This is not very high-tech,
            # but if a task has been retried for rate-limiting reasons, then we sleep
            # for a period of time between all emails within this task.  Choice of
            # the value depends on the number of workers that might be sending email in
            # parallel, and what the SES throttle rate is.
            if subtask_status.retried_nomax > 0:
                sleep(settings.BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS)

            try:
                log.info(
                    "BulkEmail ==> Task: %s, SubTask: %s, EmailId: %s, Recipient num: %s/%s, \
                    Recipient name: %s, Email address: %s",
                    parent_task_id,
                    task_id,
                    email_id,
                    recipient_num,
                    total_recipients,
                    current_recipient['profile__name'],
                    email
                )
                with dog_stats_api.timer('course_email.single_send.time.overall', tags=[_statsd_tag(course_title)]):
                    connection.send_messages([email_msg])

            except SMTPDataError as exc:
                # According to SMTP spec, we'll retry error codes in the 4xx range.  5xx range indicates hard failure.
                total_recipients_failed += 1
                log.error(
                    "BulkEmail ==> Status: Failed(SMTPDataError), Task: %s, SubTask: %s, EmailId: %s, \
                    Recipient num: %s/%s, Email address: %s",
                    parent_task_id,
                    task_id,
                    email_id,
                    recipient_num,
                    total_recipients,
                    email
                )
                if exc.smtp_code >= 400 and exc.smtp_code < 500:
                    # This will cause the outer handler to catch the exception and retry the entire task.
                    raise exc
                else:
                    # This will fall through and not retry the message.
                    log.warning(
                        'BulkEmail ==> Task: %s, SubTask: %s, EmailId: %s, Recipient num: %s/%s, \
                        Email not delivered to %s due to error %s',
                        parent_task_id,
                        task_id,
                        email_id,
                        recipient_num,
                        total_recipients,
                        email,
                        exc.smtp_error
                    )
                    dog_stats_api.increment('course_email.error', tags=[_statsd_tag(course_title)])
                    subtask_status.increment(failed=1)

            except SINGLE_EMAIL_FAILURE_ERRORS as exc:
                # This will fall through and not retry the message.
                total_recipients_failed += 1
                log.error(
                    "BulkEmail ==> Status: Failed(SINGLE_EMAIL_FAILURE_ERRORS), Task: %s, SubTask: %s, \
                    EmailId: %s, Recipient num: %s/%s, Email address: %s, Exception: %s",
                    parent_task_id,
                    task_id,
                    email_id,
                    recipient_num,
                    total_recipients,
                    email,
                    exc
                )
                dog_stats_api.increment('course_email.error', tags=[_statsd_tag(course_title)])
                subtask_status.increment(failed=1)

            else:
                total_recipients_successful += 1
                log.info(
                    "BulkEmail ==> Status: Success, Task: %s, SubTask: %s, EmailId: %s, \
                    Recipient num: %s/%s, Email address: %s,",
                    parent_task_id,
                    task_id,
                    email_id,
                    recipient_num,
                    total_recipients,
                    email
                )
                dog_stats_api.increment('course_email.sent', tags=[_statsd_tag(course_title)])
                if settings.BULK_EMAIL_LOG_SENT_EMAILS:
                    log.info('Email with id %s sent to %s', email_id, email)
                else:
                    log.debug('Email with id %s sent to %s', email_id, email)
                subtask_status.increment(succeeded=1)

            # Pop the user that was emailed off the end of the list only once they have
            # successfully been processed.  (That way, if there were a failure that
            # needed to be retried, the user is still on the list.)
            recipients_info[email] += 1
            to_list.pop()

        log.info(
            "BulkEmail ==> Task: %s, SubTask: %s, EmailId: %s, Total Successful Recipients: %s/%s, \
            Failed Recipients: %s/%s",
            parent_task_id,
            task_id,
            email_id,
            total_recipients_successful,
            total_recipients,
            total_recipients_failed,
            total_recipients
        )
        duplicate_recipients = ["{0} ({1})".format(email, repetition)
                                for email, repetition in recipients_info.most_common() if repetition > 1]
        if duplicate_recipients:
            log.info(
                "BulkEmail ==> Task: %s, SubTask: %s, EmailId: %s, Total Duplicate Recipients [%s]: [%s]",
                parent_task_id,
                task_id,
                email_id,
                len(duplicate_recipients),
                ', '.join(duplicate_recipients)
            )

    except INFINITE_RETRY_ERRORS as exc:
        dog_stats_api.increment('course_email.infinite_retry', tags=[_statsd_tag(course_title)])
        # Increment the "retried_nomax" counter, update other counters with progress to date,
        # and set the state to RETRY:
        subtask_status.increment(retried_nomax=1, state=RETRY)
        return _submit_for_retry(
            entry_id, email_id, to_list, global_email_context, exc, subtask_status, skip_retry_max=True
        )

    except LIMITED_RETRY_ERRORS as exc:
        # Errors caught here cause the email to be retried.  The entire task is actually retried
        # without popping the current recipient off of the existing list.
        # Errors caught are those that indicate a temporary condition that might succeed on retry.
        dog_stats_api.increment('course_email.limited_retry', tags=[_statsd_tag(course_title)])
        # Increment the "retried_withmax" counter, update other counters with progress to date,
        # and set the state to RETRY:
        subtask_status.increment(retried_withmax=1, state=RETRY)
        return _submit_for_retry(
            entry_id, email_id, to_list, global_email_context, exc, subtask_status, skip_retry_max=False
        )

    except BULK_EMAIL_FAILURE_ERRORS as exc:
        dog_stats_api.increment('course_email.error', tags=[_statsd_tag(course_title)])
        num_pending = len(to_list)
        log.exception(('Task %s: email with id %d caused send_course_email task to fail '
                       'with "fatal" exception.  %d emails unsent.'),
                      task_id, email_id, num_pending)
        # Update counters with progress to date, counting unsent emails as failures,
        # and set the state to FAILURE:
        subtask_status.increment(failed=num_pending, state=FAILURE)
        return subtask_status, exc

    except Exception as exc:  # pylint: disable=broad-except
        # Errors caught here cause the email to be retried.  The entire task is actually retried
        # without popping the current recipient off of the existing list.
        # These are unexpected errors.  Since they might be due to a temporary condition that might
        # succeed on retry, we give them a retry.
        dog_stats_api.increment('course_email.limited_retry', tags=[_statsd_tag(course_title)])
        log.exception(('Task %s: email with id %d caused send_course_email task to fail '
                       'with unexpected exception.  Generating retry.'),
                      task_id, email_id)
        # Increment the "retried_withmax" counter, update other counters with progress to date,
        # and set the state to RETRY:
        subtask_status.increment(retried_withmax=1, state=RETRY)
        return _submit_for_retry(
            entry_id, email_id, to_list, global_email_context, exc, subtask_status, skip_retry_max=False
        )

    else:
        # All went well.  Update counters with progress to date,
        # and set the state to SUCCESS:
        subtask_status.increment(state=SUCCESS)
        # Successful completion is marked by an exception value of None.
        return subtask_status, None
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


def _submit_for_retry(entry_id, email_id, to_list, global_email_context,
                      current_exception, subtask_status, skip_retry_max=False):
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
    task_id = subtask_status.task_id
    log.info("Task %s: Successfully sent to %s users; failed to send to %s users (and skipped %s users)",
             task_id, subtask_status.succeeded, subtask_status.failed, subtask_status.skipped)

    # Calculate time until we retry this task (in seconds):
    # The value for max_retries is increased by the number of times an "infinite-retry" exception
    # has been retried.  We want the regular retries to trigger max-retry checking, but not these
    # special retries.  So we count them separately.
    max_retries = _get_current_task().max_retries + subtask_status.retried_nomax
    base_delay = _get_current_task().default_retry_delay
    if skip_retry_max:
        # once we reach five retries, don't increase the countdown further.
        retry_index = min(subtask_status.retried_nomax, 5)
        exception_type = 'sending-rate'
        # if we have a cap, after all, apply it now:
        if hasattr(settings, 'BULK_EMAIL_INFINITE_RETRY_CAP'):
            retry_cap = settings.BULK_EMAIL_INFINITE_RETRY_CAP + subtask_status.retried_withmax
            max_retries = min(max_retries, retry_cap)
    else:
        retry_index = subtask_status.retried_withmax
        exception_type = 'transient'

    # Skew the new countdown value by a random factor, so that not all
    # retries are deferred by the same amount.
    countdown = ((2 ** retry_index) * base_delay) * random.uniform(.75, 1.25)

    log.warning(('Task %s: email with id %d not delivered due to %s error %s, '
                 'retrying send to %d recipients in %s seconds (with max_retry=%s)'),
                task_id, email_id, exception_type, current_exception, len(to_list), countdown, max_retries)

    # we make sure that we update the InstructorTask with the current subtask status
    # *before* actually calling retry(), to be sure that there is no race
    # condition between this update and the update made by the retried task.
    update_subtask_status(entry_id, task_id, subtask_status)

    # Now attempt the retry.  If it succeeds, it returns a RetryTaskError that
    # needs to be returned back to Celery.  If it fails, we return the existing
    # exception.
    try:
        retry_task = send_course_email.retry(
            args=[
                entry_id,
                email_id,
                to_list,
                global_email_context,
                subtask_status.to_dict(),
            ],
            exc=current_exception,
            countdown=countdown,
            max_retries=max_retries,
            throw=True,
        )
        raise retry_task
    except RetryTaskError as retry_error:
        # If the retry call is successful, update with the current progress:
        log.info(
            u'Task %s: email with id %d caused send_course_email task to retry again.',
            task_id,
            email_id
        )
        return subtask_status, retry_error
    except Exception as retry_exc:  # pylint: disable=broad-except
        # If there are no more retries, because the maximum has been reached,
        # we expect the original exception to be raised.  We catch it here
        # (and put it in retry_exc just in case it's different, but it shouldn't be),
        # and update status as if it were any other failure.  That means that
        # the recipients still in the to_list are counted as failures.
        log.exception(u'Task %s: email with id %d caused send_course_email task to fail to retry. To list: %s',
                      task_id, email_id, [i['email'] for i in to_list])
        num_failed = len(to_list)
        subtask_status.increment(failed=num_failed, state=FAILURE)
        return subtask_status, retry_exc


def _statsd_tag(course_title):
    """
    Prefix the tag we will use for DataDog.
    The tag also gets modified by our dogstats_wrapper code.
    """
    return u"course_email:{0}".format(course_title)
