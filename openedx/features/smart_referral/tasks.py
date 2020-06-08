from celery.task import task
from django.conf import settings

from common.lib.mandrill_client.client import MandrillClient


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_referral_and_toolkit_emails(contact_emails, user_email):
    """Send initial referral email to all contact emails and send toolkit email to referrer."""
    for email in contact_emails:
        MandrillClient().send_mail(MandrillClient.REFERRAL_INITIAL_EMAIL, email, context={
            'root_url': settings.LMS_ROOT_URL,
        })

    MandrillClient().send_mail(MandrillClient.REFERRAL_SOCIAL_IMPACT_TOOLKIT, user_email, context={})
