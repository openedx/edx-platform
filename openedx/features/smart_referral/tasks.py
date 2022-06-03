"""
Celery tasks for smart_referral app
"""
from celery.task import task
from django.conf import settings

from common.lib.hubspot_client.client import HubSpotClient
from common.lib.hubspot_client.tasks import task_send_hubspot_email
from openedx.features.smart_referral.models import SmartReferral


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_referral_and_toolkit_emails(contact_emails, user_email):
    """Send initial referral email to all contact emails and send toolkit email to referrer."""
    for email in contact_emails:
        referral_email_context = {
            'emailId': HubSpotClient.REFERRAL_INITIAL_EMAIL,
            'message': {
                'to': email
            },
            'customProperties': {
                'root_url': settings.LMS_ROOT_URL,
            }
        }
        task_send_hubspot_email.delay(referral_email_context)

    referral_social_email_context = {
        'emailId': HubSpotClient.REFERRAL_SOCIAL_IMPACT_TOOLKIT,
        'message': {
            'to': user_email
        }
    }
    task_send_hubspot_email.delay(referral_social_email_context)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_referral_follow_up_emails(contact_email_list):
    """Send follow-up referral email to contact email."""
    for contact_email in contact_email_list:
        context = {
            'emailId': HubSpotClient.REFERRAL_FOLLOW_UP_EMAIL,
            'message': {
                'to': contact_email
            },
            'customProperties': {
                'root_url': settings.LMS_ROOT_URL,
            }
        }
        task_send_hubspot_email.delay(context)
        SmartReferral.objects.filter(contact_email=contact_email).update(is_referral_step_complete=True)
