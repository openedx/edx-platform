from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = \
''' Extract an e-mail list of all active students. '''

    def handle(self, *args, **options):
        #text = open(args[0]).read()
        #subject = open(args[1]).read()
        users = User.objects.all()

        for user in users:
            if user.is_active:
                print user.email
