import json
import logging

from django.core.management.base import BaseCommand

from openedx.core.djangoapps.appsembler.sites.utils import make_amc_admin, reset_tokens


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
                            dest='org',
                            help='The organization name or short name.')

    def handle(self, *args, **options):
        make_amc_admin(user=options['user'], org_name=options['org'])
        tokens = reset_tokens(user=options['user'])
        self.stdout.write(json.dumps(tokens))
