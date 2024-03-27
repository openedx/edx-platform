"""
Management command for sending email digest
"""
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.notifications.email.tasks import send_digest_email_to_all_users


class Command(BaseCommand):
    """
    Invoke with:

        python manage.py lms send_email_digest [cadence_type]
        cadence_type: Daily or Weekly
    """
    help = (
        "Send email digest to user."
    )

    def add_arguments(self, parser):
        """
        Adds management commands parser arguments
        """
        parser.add_argument('cadence_type', choices=['Daily', 'Weekly'])

    def handle(self, *args, **kwargs):
        """
        Start task to send email digest to users
        """
        send_digest_email_to_all_users.delay(args=(kwargs['cadence_type'],))
