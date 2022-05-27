"""
Celery tasks for smart_referral app
"""
from celery.task import task
from django.conf import settings

from common.lib.mandrill_client.client import MandrillClient
from openedx.features.smart_referral.models import SmartReferral


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_referral_and_toolkit_emails(contact_emails, user_email):
    """Send initial referral email to all contact emails and send toolkit email to referrer."""
    return

    # TODO: FIX MANDRILL EMAILS
    mandrill_client = MandrillClient()

    for email in contact_emails:
        mandrill_client.send_mail(MandrillClient.REFERRAL_INITIAL_EMAIL, email, context={
            'root_url': settings.LMS_ROOT_URL,
        })

    mandrill_client.send_mail(MandrillClient.REFERRAL_SOCIAL_IMPACT_TOOLKIT, user_email, context={})


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_referral_follow_up_emails(contact_email_list):
    """Send follow-up referral email to contact email."""
    return

    # TODO: FIX MANDRILL EMAILS
    for contact_email in contact_email_list:
        response = MandrillClient().send_mail(MandrillClient.REFERRAL_FOLLOW_UP_EMAIL, contact_email, context={
            'root_url': settings.LMS_ROOT_URL,
        })
        if response[0]['status'] == 'sent':
            SmartReferral.objects.filter(contact_email=response[0]['email']).update(is_referral_step_complete=True)
