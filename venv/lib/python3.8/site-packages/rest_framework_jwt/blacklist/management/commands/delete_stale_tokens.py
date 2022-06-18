from django.core.management.base import BaseCommand

from rest_framework_jwt.blacklist.models import BlacklistedToken


class Command(BaseCommand):
    help = 'Deletes any expired Blacklisted tokens'

    def handle(self, *args, **kwargs):
        BlacklistedToken.objects.delete_stale_tokens()
