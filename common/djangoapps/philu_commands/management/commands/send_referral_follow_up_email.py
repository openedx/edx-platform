from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from openedx.features.smart_referral.models import SmartReferral
from openedx.features.smart_referral.tasks import task_send_referral_follow_up_emails

CONTACT_EMAIL = 'contact_email'
DAYS_TO_SEND_FOLLOW_UP_EMAIL = 3


class Command(BaseCommand):
    help = """
    Send follow-up referral email to all those contacts which are at least 3 days old, are not registered on our
    platform, and have not received follow-up email.
    """

    def handle(self, *args, **options):
        emails_list = []
        referral_threshold_date = timezone.now() - timedelta(days=DAYS_TO_SEND_FOLLOW_UP_EMAIL)

        pending_referral_emails = SmartReferral.objects.filter(
            created__lte=referral_threshold_date,
            is_referral_step_complete=False
        ).values_list(
            CONTACT_EMAIL,
            flat=True
        ).distinct()

        for referral_email in pending_referral_emails:
            try:
                User.objects.get(email=referral_email)
                SmartReferral.objects.filter(contact_email=referral_email).update(
                    is_referral_step_complete=True
                )
            except User.DoesNotExist:
                emails_list.append(referral_email)

        if emails_list:
            task_send_referral_follow_up_emails(emails_list)
