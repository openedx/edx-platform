import json
import logging

from django.db.models.query import Q
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from openedx.core.djangoapps.appsembler.sites.utils import make_amc_admin


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
        user = get_user_model().objects.get(Q(email=options['user']) | Q(username=options['user']))
        details = make_amc_admin(user=user, org_name=options['org'])
        self.stdout.write(json.dumps(details, cls=DjangoJSONEncoder))
