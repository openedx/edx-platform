import json
import logging

from django.conf import settings
from edx_ace import ace
from edx_ace.recipient import Recipient
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.features.ucsd_features.message_types import SupportNotification

log = logging.getLogger(__name__)
TEMPLATE_PATH = '{key}_email.html'


def send_notification(message_type, data, subject, dest_emails):
    """
    Send an email

    Arguments:
        message_type - string value to select ace message object
        data - Dict containing context/data for the template
        subject - Email subject
        dest_emails - List of destination emails

    Returns:
        a boolean variable indicating email response.
    """
    message_types = {
        'support': SupportNotification,
    }
    current_site = get_current_site()
    content = json.dumps(data)
    data.update(
        {
            'subject': subject,
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
            log.error(
                'Unable to send an email to %s for content "%s".',
                email,
                content
            )
    return return_value


def send_notification_email_to_support(subject, body, name, email, custom_fields=None, additional_info=None, course=None):
    """
    Sending a notification-email to the Support Team.
    """
    key = "support"
    dest_emails = settings.SUPPORT_DESK_EMAILS
    data = {
        'name': name,
        'email': email,
        'body': body,
        'custom_fields': custom_fields,
        'additional_info': additional_info,
    }
    email_response = send_notification(key, data, subject, dest_emails)
    return email_response
