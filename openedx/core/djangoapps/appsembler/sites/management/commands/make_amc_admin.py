import json
import logging

from django.core.management.base import BaseCommand

from openedx.core.djangoapps.appsembler.sites.utils import reset_tokens, ensure_amc_site_admin


log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Refresh both AMC access and refresh token, '
        'make the user AMC site admin and print those tokens. '
        'This command fixes the spinner issue.'
    )

    def add_arguments(self, parser):
        parser.add_argument('-u', '--user',
                            action='store',
                            dest='user',
                            help='Username or email for the AMC admin.')
        parser.add_argument('-o', '--org',
                            action='store',
                            dest='commit',
                            help='The organization name or short name.')

    def handle(self, user, org):
        tokens = reset_tokens(user, org)
        ensure_amc_site_admin(user, org)
        self.stdout.write(json.dumps(tokens))
