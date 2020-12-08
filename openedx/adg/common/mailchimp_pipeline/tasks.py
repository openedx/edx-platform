"""
Tasks for Mailchimp pipeline
"""
import logging

from celery.task import task
from django.conf import settings

from .client import MailchimpClient

log = logging.getLogger(__name__)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_user_info_to_mailchimp(user_email, user_json):
    """
    Sync user data to Mailchimp (audience) list

    Args:
        user_email (str): User email which needs to be updated
        user_json (dict): User updated data.

    Returns:
        None
    """
    MailchimpClient().create_or_update_list_member(email=user_email, data=user_json)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_user_enrollments_to_mailchimp(user_email, user_json):
    """
    Update member info on Mailchimp (audience) list, related to course. Add course enrollment title
    and course short id to member contact info on Mailchimp.

    Args:
        user_email (str): user email
        user_json (dict): User data to sync

    Returns:
        None
    """
    MailchimpClient().create_or_update_list_member(email=user_email, data=user_json)
