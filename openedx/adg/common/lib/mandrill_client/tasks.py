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
def task_send_mandrill_email(template, emails, context):
    """
    Sends an email by calling send_mandrill_email, asynchronously

    Arguments:
        template (str): String containing template id
        emails (iterable): Email addresses of users
        context (dict): Dictionary containing email content

    Returns:
        None
    """
    log.info(f'Sending an email using template: {template} to accounts: {emails}, from inside task_send_mandrill_email')

    template_to_email_adresses_map = defaultdict(list)
    for email in emails:
        template_slug = add_user_preferred_language_to_template_slug(template, email)
        template_to_email_adresses_map[template_slug].append({'email': email})

    for template_slug, recipient_emails in template_to_email_adresses_map.items():
        MandrillClient().send_mandrill_email(template_slug, recipient_emails, context)
