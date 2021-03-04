"""
Tasks for Mandrill client
"""
from celery.task import task

from .client import MandrillClient


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
    MandrillClient().send_mandrill_email(template, email, context)
