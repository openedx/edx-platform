"""
Tasks for Mandrill client
"""
import logging

from celery.task import task

from .client import MandrillClient

log = logging.getLogger(__name__)


@task()
def task_send_mandrill_email(template, email, context):
    """
    Sends an email by calling send_mandrill_email, asynchronously

    Arguments:
        template (str): String containing template id
        email (str): Email address of user
        context (dict): Dictionary containing email content

    Returns:
        None
    """
    log.info(
        'Preparing to send an email using template: %s to account: %s, from inside task_send_mandrill_email',
        template,
        email
    )

    MandrillClient().send_mandrill_email(template, email, context)
