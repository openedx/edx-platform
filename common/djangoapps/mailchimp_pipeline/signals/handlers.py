"""
Handlers and signals for Mailchimp pipeline
"""
from logging import getLogger

from celery.task import task
from django.conf import settings
from common.lib.hubspot_client.client import HubSpotClient


log = getLogger(__name__)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_account_activation_email(data):
    """
    Task that sends the account activation email containing the given data

    Arguments:
        data: Object containing the details for the activation email

    Returns:
        None
    """
    context = {
        'emailId': HubSpotClient.ACCOUNT_ACTIVATION_EMAIL,
        'message': {
            'to': data['user_email']
        },
        'customProperties': {
            'first_name': data['first_name'],
            'activation_link': data['activation_link'],
        }
    }

    HubSpotClient().send_mail(context)
