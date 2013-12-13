"""
Send emails to users inviting them to add their course certificates to their
LinkedIn profiles.
"""

import json

from django.core.management.base import BaseCommand
from optparse import make_option

from certificates.models import GeneratedCertificate
from ...models import LinkedIn


class Command(BaseCommand):
    """
    Django command for inviting users to add their course certificates to their
    LinkedIn profiles.
    """
    args = ''
    help = ('Sends emails to edX users that are on LinkedIn who have completed '
            'course certificates, inviting them to add their certificates to '
            'their LinkedIn profiles')
    option_list = BaseCommand.option_list + (
        make_option(
            '--grandfather',
            action='store_true',
            dest='grandfather',
            default=False,
            help="Creates aggregate invitations for all certificates a user "
                 "has earned to date and sends a 'grandfather' email.  This is "
                 "intended to be used when the feature is launched to invite "
                 "all users that have earned certificates to date to add their "
                 "certificates.  Afterwards the default, one email per "
                 "certificate mail form will be used."),)

    def handle(self, *args, **options):
        grandfather = options.get('grandfather', False)
        accounts = LinkedIn.objects.filter(has_linkedin_account=True)
        for account in accounts:
            emailed = json.loads(account.emailed_courses)
            user = account.user
            certificates = GeneratedCertificate.objects.filter(user=user)
            certificates = certificates.filter(status='downloadable')
            certificates = [cert for cert in certificates
                            if cert.course_id not in emailed]
            if not certificates:
                continue
            if grandfather:
                send_grandfather_email(user, certificates)
                emailed.extend([cert.course_id for cert in certificates])
            else:
                for certificate in certificates:
                    send_email(user, certificate)
                    emailed.append(certificate.course_id)
            account.emailed_courses = json.dumps(emailed)


def send_grandfather_email(user, certificates):
    """
    Send the 'grandfathered' email informing historical students that they may
    now post their certificates on their LinkedIn profiles.
    """
    print "GRANDFATHER: ", user, certificates


def send_email(user, certificate):
    """
    Email a user that recently earned a certificate, inviting them to post their
    certificate on their LinkedIn profile.
    """
    print "EMAIL: ", user, certificate
