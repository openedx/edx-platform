from django.core.management.base import BaseCommand
from mailchimp_pipeline.client import ChimpClient
from django.contrib.auth.models import User
from django.conf import settings

from logging import getLogger
log = getLogger(__name__)


class Command(BaseCommand):
    help = """
    Delete user from mail chimp learners list
        manage.py delete_users_from_mailchimp
    """

    def handle(self, *args, **options):
        client = ChimpClient()

        users = User.objects.all()
        for user in users:
            client.delete_user_from_list(settings.MAILCHIMP_LEARNERS_LIST_ID, user.email)

        pass
