"""
HubSpot client tasks
"""
from celery.task import task

from common.lib.hubspot_client.client import HubSpotClient


@task()
def task_send_hubspot_email(data):
    """
    Task to send email using HubSpot Client.
    """
    HubSpotClient().send_mail(data)
