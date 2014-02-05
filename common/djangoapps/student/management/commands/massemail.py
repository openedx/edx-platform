from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from edxmako import lookup_template


class Command(BaseCommand):
    help = \
'''Sends an e-mail to all users. Takes a single
parameter -- name of e-mail template -- located
in templates/email. Adds a .txt for the message
body, and an _subject.txt for the subject. '''

    def handle(self, *args, **options):
        #text = open(args[0]).read()
        #subject = open(args[1]).read()
        users = User.objects.all()
        text = lookup_template('main', 'email/' + args[0] + ".txt").render()
        subject = lookup_template('main', 'email/' + args[0] + "_subject.txt").render().strip()
        for user in users:
            if user.is_active:
                user.email_user(subject, text)
