"""
Tasks for Mandrill client
"""
import logging
from collections import defaultdict

from celery.task import task

from openedx.adg.common.lib.mandrill_client.helpers import add_user_preferred_language_to_template_slug

from .client import MandrillClient

log = logging.getLogger(__name__)


@task()
def task_send_mandrill_email(template, emails, context, send_at=None, save_mandrill_msg_ids=False):
    """
    Sends an email by calling send_mandrill_email, asynchronously

    Arguments:
        template (str): String containing template id
        emails (iterable): Email addresses of users
        context (dict): Dictionary containing email content
        send_at (str): When this message should be sent as a UTC timestamp in YYYY-MM-DD HH:MM:SS format.
        save_mandrill_msg_ids (bool): Whether to process mandrill response and save message ids or not

    Returns:
        None
    """
    log.info(f'Sending an email using template: {template} to accounts: {emails}, from inside task_send_mandrill_email')

    template_to_email_adresses_map = defaultdict(list)
    for email in emails:
        template_slug = add_user_preferred_language_to_template_slug(template, email)
        template_to_email_adresses_map[template_slug].append({'email': email})

    for template_slug, recipient_emails in template_to_email_adresses_map.items():
        response = MandrillClient().send_mandrill_email(template_slug, recipient_emails, context, send_at)

        if response and save_mandrill_msg_ids:
            from openedx.adg.lms.webinars.helpers import save_scheduled_reminder_ids

            save_scheduled_reminder_ids(response, template, context)


@task()
def task_cancel_mandrill_emails(msg_ids):
    """
    Cancels scheduled msgs on mandrill.

    Args:
        msg_ids (list): List of Ids of the scheduled emails on mandrill.
    """
    for msg_id in msg_ids:
        log.info(f'Cancelling a scheduled email, mandrill msg_id: {msg_id}')
        MandrillClient().cancel_scheduled_email(msg_id)
