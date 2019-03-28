
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        user = User.objects.get(username=options['username'])
        token, created = Token.objects.get_or_create(user=user)
        self.stdout.write('token key: "{}"'.format(token.key))
        self.stdout.write('user: "{}"'.format(token.user.username))
