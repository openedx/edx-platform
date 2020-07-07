from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from openedx.features.smart_referral.models import SmartReferral
from openedx.features.smart_referral.tasks import task_send_referral_follow_up_email

CONTACT_EMAIL = 'contact_email'
DAYS_TO_SEND_FOLLOW_UP_EMAIL = 3


class Command(BaseCommand):
    help = """
    Send follow up referral email to all those contacts
    """

    def handle(self, *args, **options):
        emails_list = []
        three_days_old_date = timezone.now().date() - timedelta(days=DAYS_TO_SEND_FOLLOW_UP_EMAIL)

        three_days_old_referral = SmartReferral.objects.filter(
            created__date__lte=three_days_old_date,
            is_referral_step_complete=False
        ).values(
            CONTACT_EMAIL
        )
        for referral in three_days_old_referral:
            try:
                User.objects.get(email=referral[CONTACT_EMAIL])
                SmartReferral.objects.filter(contact_email=referral[CONTACT_EMAIL]).update(
                    is_referral_step_complete=True
                )
            except User.DoesNotExist:
                emails_list.append(referral[CONTACT_EMAIL])

        if emails_list:
            task_send_referral_follow_up_email(emails_list)
