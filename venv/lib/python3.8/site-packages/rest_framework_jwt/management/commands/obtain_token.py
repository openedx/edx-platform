import sys

from django.conf import settings
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create new jwt token for the requested user during development'

    def add_arguments(self, parser):
        parser.add_argument(dest='pk', type=str, help="User's primary key")

    def handle(self, pk, *args, **options):
        try:
            if getattr(settings, "DEBUG") is False:
                raise CommandError("obtain_token.py command requires DEBUG=True ")
            user = get_user_model().objects.filter(pk=pk).first()
            if user is None:
                raise CommandError("There is no user with the given pk")

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            self.stdout.write(token)
        except CommandError as exp:
            self.stderr.write("Unable to obtain token because {}".format(str(exp)))
            sys.exit(1)
