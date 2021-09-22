import json
import logging

from edx_ace import ace
from edx_ace.recipient import Recipient
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.wikimedia_features.email import message_types

logger = logging.getLogger(__name__)


MESSAGE_TYPES = {
  'pending_messages': message_types.PendingMessagesNotification,
}


def send_ace_message(request_user, request_site, dest_email, context, message_class):
    with emulate_http_request(site=request_site, user=request_user):
        message = message_class().personalize(
            recipient=Recipient(lms_user_id=0, email_address=dest_email),
            language='en',
            user_context=context,
        )
        logger.info('Sending email notification with context %s', context)
        ace.send(message)


def send_notification(message_type, data, subject, dest_emails, request_user, current_site=None):
    """
    Send an email
    Arguments:
        message_type - string value to select ace message object
        data - Dict containing context/data for the template
        subject - Email subject
        dest_emails - List of destination emails
    Returns:
        a boolean variable indicating email response.
        if email is successfully send to all dest emails -> return True otherwise return false.
    """
    if not current_site:
        current_site = Site.objects.all().first()

    data.update({'subject': subject})

    message_context = get_base_template_context(current_site)
    message_context.update(data)
    content = json.dumps(message_context)

    message_class = MESSAGE_TYPES[message_type]
    return_value = True

    base_root_url = current_site.configuration.get_value('LMS_ROOT_URL')
    logo_path = current_site.configuration.get_value('LOGO', settings.DEFAULT_LOGO)

    message_context.update({
        "site_name":  current_site.configuration.get_value('platform_name'),
        "logo_url": u'{base_url}{logo_path}'.format(base_url=base_root_url, logo_path=logo_path),
        "messenger_url": u'{base_url}{messenger_path}'.format(base_url=base_root_url, messenger_path=reverse("messenger:messenger_home"))
    })

    for email in dest_emails:
        message_context.update({
            "email": email
        })
        try:
            send_ace_message(request_user, current_site, email, message_context, message_class)
            logger.info(
                'Email has been sent to "%s" for content %s.',
                email,
                content
            )
        except Exception as e:
            logger.error(
                'Unable to send an email to %s for content "%s".',
                email,
                content,
            )
            logger.error(e)
            return_value = False

    return return_value


def send_unread_messages_email(user, user_context, request_user):
    subject = "Unread Messages"
    logger.info("Sending messenger pending msgs email to the users: {}".format(user))
    key = "pending_messages"
    name = user.username
    if user.first_name:
        name = user.first_name + " " + user.last_name
    data = {"name": name,}
    data.update(user_context)
    send_notification(key, data, subject, [user.email], request_user)
