import os.path
import time

from django.core.management.base import BaseCommand
from django.conf import settings

import mitxmako

from django.core.mail import send_mass_mail
import sys

import datetime


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


class Command(BaseCommand):
    help = \
'''Sends an e-mail to all users in a text file.
E.g.
manage.py userlist.txt message logfile.txt rate
userlist.txt -- list of all users
message -- prefix for template with message
logfile.txt -- where to log progress
rate -- messages per second
 '''
    log_file = None

    def hard_log(self, text):
        self.log_file.write(datetime.datetime.utcnow().isoformat() + ' -- ' + text + '\n')

    def handle(self, *args, **options):
        (user_file, message_base, logfilename, ratestr) = args

        users = [u.strip() for u in open(user_file).readlines()]

        message = mitxmako.lookup['main'].get_template('emails/' + message_base + "_body.txt").render()
        subject = mitxmako.lookup['main'].get_template('emails/' + message_base + "_subject.txt").render().strip()
        rate = int(ratestr)

        self.log_file = open(logfilename, "a+", buffering=0)

        i = 0
        for users in chunks(users, rate):
            emails = [(subject, message, settings.DEFAULT_FROM_EMAIL, [u]) for u in users]
            self.hard_log(" ".join(users))
            send_mass_mail(emails, fail_silently=False)
            time.sleep(1)
            print datetime.datetime.utcnow().isoformat(), i
            i = i + len(users)
            # Emergency interruptor
            if os.path.exists("/tmp/stopemails.txt"):
                self.log_file.close()
                sys.exit(-1)
        self.log_file.close()
