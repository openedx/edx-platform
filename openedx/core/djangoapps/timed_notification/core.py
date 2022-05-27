import logging

from lms.djangoapps.courseware.access import has_access
from opaque_keys.edx.locations import SlashSeparatedCourseKey
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
from lms.djangoapps.courseware.courses import get_course_by_id
from xmodule.modulestore.django import modulestore

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

            # TODO: FIX MANDRILL EMAILS
            # MandrillClient().send_mail(template_name, email, context)
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
    base_url = settings.LMS_ROOT_URL
    return base_url + course_link


def get_course_first_chapter_link(course, request=None):
    """
    Helper function to get first chapter link in course enrollment email
    """
    from lms.djangoapps.philu_overrides.courseware.views.views import get_course_related_keys
    from lms.djangoapps.courseware.views.views import get_last_accessed_courseware

    if not request:

        course_desc = get_course_by_id(course.id)
        first_chapter_url = ''
        first_section = ''
        if course_desc.get_children():
            first_chapter_url = course_desc.get_children()[0].scope_ids.usage_id.block_id
            if course_desc.get_children()[0].get_children():
                first_section = course_desc.get_children()[0].get_children()[0].scope_ids.usage_id.block_id

        course_target = reverse(
            'courseware_section',
            args=[course.id.to_deprecated_string(),
                  first_chapter_url,
                  first_section]
        )

        base_url = settings.LMS_ROOT_URL
        return base_url + course_target
    else:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(
            course.id.to_deprecated_string())
        with modulestore().bulk_operations(course_key):
            if has_access(request.user, 'load', course):
                access_link = get_last_accessed_courseware(
                    get_course_by_id(course_key, 0),
                    request,
                    request.user
                )

                first_chapter_url, first_section = get_course_related_keys(
                    request, get_course_by_id(course_key, 0))
                first_target = reverse('courseware_section', args=[
                    course.id.to_deprecated_string(),
                    first_chapter_url,
                    first_section
                ])

                course_target = access_link if access_link is not None else first_target
            else:
                course_target = '/courses/' + course.id.to_deprecated_string()
        return course_target
