import logging

from student.models import CourseEnrollment
from edxmako.shortcuts import render_to_string

from django.core.urlresolvers import reverse
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings

from collections import Counter
from smtplib import SMTPDataError
from boto.ses.exceptions import (
    SESAddressBlacklistedError,
    SESDomainEndsWithDotError,
    SESLocalAddressCharacterError,
    SESIllegalAddressError,
)

log = logging.getLogger('edx.celery.task')

# Errors that an individual email is failing to be sent, and should just
# be treated as a fail.
SINGLE_EMAIL_FAILURE_ERRORS = (
    SESAddressBlacklistedError,  # Recipient's email address has been temporarily blacklisted.
    SESDomainEndsWithDotError,  # Recipient's email address' domain ends with a period/dot.
    SESIllegalAddressError,  # Raised when an illegal address is encountered.
    SESLocalAddressCharacterError,  # An address contained a control or whitespace character.
)


def send_course_notification_email(course, mako_template_path, context, to_list=None):

    """
    Sends an email to a list of recipients.

    Inputs are:
      * `course`: notification about this course.
      * `mako_template_path`: Mako template path.
      * `context`: context for template
      * `to_list`: list of recipients, if list is not provided then the email will be send to all enrolled students.

    """

    log.info("Sending email for course %s", course)
    if to_list is None:
        to_list = CourseEnrollment.objects.users_enrolled_in(course.id)
    log.info("Users list %s", to_list)
    total_recipients = len(to_list)
    recipient_num = 0
    total_recipients_successful = 0
    total_recipients_failed = 0
    log.info("Setting up reference of user information")
    recipients_info = Counter()

    log.info(
        "TimedNotification ==> TotalRecipients: %s",
        total_recipients
    )

    try:
        log.info("Getting email connection")
        connection = get_connection()
        log.info("Opening email connection")
        connection.open()

        log.info("Before loop through to the user-list")
        for current_recipient in to_list:
            recipient_num += 1
            log.info("Getting user email")
            email = current_recipient.email
            log.info("Setting up subject of the email")
            subject = settings.NOTIFICATION_EMAIL_SUBJECT
            log.info("Adding full name in the context")
            context['full_name'] = current_recipient.extended_profile.first_name + " " + current_recipient.\
                extended_profile.last_name
            log.info("Constructing email template")
            template = render_to_string(mako_template_path, context)
            log.info("Instantiating email message")
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=template,
                from_email=settings.NOTIFICATION_FROM_EMAIL,
                to=[email],
                connection=connection
            )
            log.info("Adding html template")
            email_msg.attach_alternative(template, 'text/html')

            try:
                log.info(
                    "TimedNotification ==> Recipient num: %s/%s, Recipient name: %s, Email address: %s",
                    recipient_num,
                    total_recipients,
                    current_recipient.username,
                    email
                )
                log.info("Just before sending email")
                connection.send_messages([email_msg])
                log.info("After sending email")

            except SMTPDataError as exc:
                # According to SMTP spec, we'll retry error codes in the 4xx range.  5xx range indicates hard failure.
                total_recipients_failed += 1
                log.error(
                    "TimedNotification ==> Status: Failed(SMTPDataError), Recipient num: %s/%s, Email address: %s",
                    recipient_num,
                    total_recipients,
                    email
                )
                if exc.smtp_code >= 400 and exc.smtp_code < 500:
                    raise exc
                else:
                    # This will fall through and not retry the message.
                    log.warning(
                        'TimedNotification ==> Recipient num: %s/%s, Email not delivered to %s due to error %s',
                        recipient_num,
                        total_recipients,
                        email,
                        exc.smtp_error
                    )

            except SINGLE_EMAIL_FAILURE_ERRORS as exc:
                # This will fall through and not retry the message.
                total_recipients_failed += 1
                log.error(
                    "TimedNotification ==> Status: Failed(SINGLE_EMAIL_FAILURE_ERRORS), Recipient num: %s/%s, \
                    Email address: %s, Exception: %s",
                    recipient_num,
                    total_recipients,
                    email,
                    exc
                )
            else:
                total_recipients_successful += 1
                log.info(
                    "TimedNotification ==> Status: Success, Recipient num: %s/%s, Email address: %s,",
                    recipient_num,
                    total_recipients,
                    email
                )
            recipients_info[email] += 1

        log.info(
            "TimedNotification ==> Total Successful Recipients: %s/%s, Failed Recipients: %s/%s",
            total_recipients_successful,
            total_recipients,
            total_recipients_failed,
            total_recipients
        )
        duplicate_recipients = ["{0} ({1})".format(email, repetition)
                                for email, repetition in recipients_info.most_common() if repetition > 1]
        if duplicate_recipients:
            log.info(
                "TimedNotification ==> Total Duplicate Recipients [%s]: [%s]",
                len(duplicate_recipients),
                ', '.join(duplicate_recipients)
            )
    finally:
        # Clean up at the end.
        connection.close()


def get_course_link(course_id):
    course_link = reverse('about_course', args=[course_id])
    course_full_link = settings.LMS_BASE_URL + course_link
    return course_full_link
