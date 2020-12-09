"""
Helper methods for applications
"""
from django.conf import settings
from django.core.validators import ValidationError
from django.urls import reverse
from django.utils.translation import ugettext as _

from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.lms.student.helpers import send_mandrill_email
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from .constants import LOGO_IMAGE_MAX_SIZE


def validate_logo_size(file_):
    """
    Validate maximum allowed file upload size, raise validation error if file size exceeds.

    Arguments:
         file_(object): file that needs to be validated for size

    Returns:
        None
    """
    size = getattr(file_, 'size', None)
    if size and LOGO_IMAGE_MAX_SIZE < size:
        raise ValidationError(_('File size must not exceed {size} KB').format(size=LOGO_IMAGE_MAX_SIZE / 1024))


def send_application_submission_confirmation_email(recipient_email):
    """
    Send an email to the recipient_email according to the mandrill template

    Args:
        recipient_email(str): target email address to send the email to

    Returns:
        None
    """
    root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    course_catalog_url = '{root_url}{course_catalog_url}'.format(
        root_url=root_url,
        course_catalog_url=reverse('courses')
    )

    context = {
        'course_catalog_url': course_catalog_url
    }
    send_mandrill_email(MandrillClient.APPLICATION_SUBMISSION_CONFIRMATION, recipient_email, context)
