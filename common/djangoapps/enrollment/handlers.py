"""
Handlers and actions related to enrollment.
"""
import logging
from smtplib import SMTPException
from urlparse import urlunsplit

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail.message import EmailMessage
from django.dispatch import receiver
from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange

LOGGER = logging.getLogger(__name__)


@receiver(ENROLL_STATUS_CHANGE)
def send_email_to_staff_on_student_enrollment(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Sends an e-mail to staff after a new enrollment.
    This feature can be enabled by setting the e-mail of the staff in ENROLLMENT_NOTIFICATION_EMAIL in lms.env.json,
    or by using a SiteConfiguration variable of the same name (which will override the env one).
    Disabled by default.
    """

    if event == EnrollStatusChange.enroll:
        to_email = configuration_helpers.get_value('ENROLLMENT_NOTIFICATION_EMAIL',
                                                   settings.ENROLLMENT_NOTIFICATION_EMAIL)

        if not to_email:
            # feature disabled
            return

        course_id = kwargs['course_id']

        site_protocol = 'https' if settings.HTTPS == 'on' else 'http'
        site_domain = configuration_helpers.get_value('site_domain', settings.SITE_NAME)
        context = {
            'user': user,
            # This full_name is dependent on edx-platform's profile implementation
            'user_full_name': user.profile.name if hasattr(user, 'profile') else None,

            'course_url': urlunsplit((
                site_protocol,
                site_domain,
                reverse('about_course', args=[course_id.to_deprecated_string()]),
                None,
                None
            )),
            'user_admin_url': urlunsplit((
                site_protocol,
                site_domain,
                reverse('admin:auth_user_change', args=[user.id]),
                None,
                None,
            )),
        }
        subject = ''.join(
            render_to_string('emails/new_enrollment_email_subject.txt', context).splitlines()
        )
        message = render_to_string('emails/new_enrollment_email_body.txt', context)

        email = EmailMessage(subject=subject, body=message, from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email])

        try:
            email.send()
        except SMTPException as exception:
            LOGGER.error("Failed sending e-mail about new enrollment to %s", to_email)
            LOGGER.exception(exception)
