import logging

from student.models import CourseEnrollment
from django.core.urlresolvers import reverse
from django.conf import settings

from collections import Counter
from boto.ses.exceptions import (
    SESAddressBlacklistedError,
    SESDomainEndsWithDotError,
    SESLocalAddressCharacterError,
    SESIllegalAddressError,
)
from common.lib.mandrill_client.client import MandrillClient
from crum import get_current_request
from util.request import safe_get_host



log = logging.getLogger('timed_notifications')

# Errors that an individual email is failing to be sent, and should just
# be treated as a fail.
SINGLE_EMAIL_FAILURE_ERRORS = (
    SESAddressBlacklistedError,  # Recipient's email address has been temporarily blacklisted.
    SESDomainEndsWithDotError,  # Recipient's email address' domain ends with a period/dot.
    SESIllegalAddressError,  # Raised when an illegal address is encountered.
    SESLocalAddressCharacterError,  # An address contained a control or whitespace character.
)


def send_course_notification_email(course, template_name, context, to_list=None):

    """
    Sends an email to a list of recipients.

    Inputs are:
      * `course`: notification about this course.
      * `template_name`: slug of the Mandrill template which is to be used.
      * `context`: context for template
      * `to_list`: list of recipients, if list is not provided then the email will be send to all enrolled students.

    """

    log.info("Sending email for course %s", course)
    if to_list is None:
        to_list = CourseEnrollment.objects.users_enrolled_in(course.id)
    log.info("Users list %s", to_list)
    total_recipients = len(to_list)
    recipient_num = 0
    log.info("Setting up reference of user information")
    recipients_info = Counter()

    log.info(
        "TimedNotification ==> TotalRecipients: %s",
        total_recipients
    )

    try:
        log.info("Before loop through to the user-list")
        for current_recipient in to_list:
            recipient_num += 1
            log.info("Getting user email")
            email = current_recipient.email
            log.info("Adding full name in the context")
            context["full_name"] = current_recipient.first_name + " " + current_recipient.last_name

            log.info(
            "TimedNotification ==> Recipient num: %s/%s, Recipient name: %s, Email address: %s",
                recipient_num,
                total_recipients,
                current_recipient.username,
                email
            )
            log.info("Just before sending email")
            MandrillClient().send_mail(template_name, email, context)
            log.info("After sending email")

            recipients_info[email] += 1

        duplicate_recipients = ["{0} ({1})".format(email, repetition)
                                for email, repetition in recipients_info.most_common() if repetition > 1]
        if duplicate_recipients:
            log.info(
                "TimedNotification ==> Total Duplicate Recipients [%s]: [%s]",
                len(duplicate_recipients),
                ', '.join(duplicate_recipients)
            )
    except Exception as e:
        log.info(e.message)
        log.info('Email send failed!')


def get_course_link(course_id):
    course_link = reverse("about_course", args=[course_id])
    base_url = settings.LMS_ROOT_URL[:-3]
    return base_url + course_link
