import json
import logging

from django.conf import settings

from edx_ace import ace
from edx_ace.recipient import Recipient
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.features.ucsd_features.message_types import CommerceSupportNotification, ContactSupportNotification

log = logging.getLogger(__name__)
TEMPLATE_PATH = '{key}_email.html'


def send_notification(message_type, data, dest_emails):
    """
    Send an email

    Arguments:
        message_type - string value to select ace message object
        data - Dict containing context/data for the template
        dest_emails - List of destination emails

    Returns:
        a boolean variable indicating email response.
    """
    message_types = {
        'contact_support': ContactSupportNotification,
        'commerce_support': CommerceSupportNotification
    }
    current_site = get_current_site()
    content = json.dumps(data)
    data.update(
        {
            'site': current_site
        }
    )
    message_context = get_base_template_context(current_site)
    message_context.update(data)
    message_class = message_types[message_type]
    return_value = False
    for email in dest_emails:
        try:
            message = message_class().personalize(
                recipient=Recipient(username='', email_address=email),
                language='en',
                user_context=message_context,
            )
            ace.send(message)
            log.info(
                'Email has been sent to "%s" for content %s.',
                email,
                content
            )
            return_value = True
        except Exception:
            log.exception(
                'Unable to send an email to %s for content "%s".',
                email,
                content
            )
    return return_value


def send_notification_email_to_support(subject, body, name, email, message_type, custom_fields=None):
    """
    Sending a notification-email to the Support Team.
    """
    course = None
    if message_type == 'contact_support':
        course = get_course_name(custom_fields)
    dest_emails = settings.SUPPORT_DESK_EMAILS
    data = {
        'subject': subject,
        'name': name,
        'email': email,
        'body': body,
        'course': course,
        'custom_fields': custom_fields
    }
    email_response = send_notification(message_type, data, dest_emails)
    return email_response


def get_course_name(custom_fields):
    course_key = custom_fields[0].get('value')
    try:
        course_name = CourseKey.from_string(course_key).course
    except InvalidKeyError:
        return None
    return course_name
