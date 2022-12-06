import inspect
import json

from openedx.core.djangoapps.appsembler.sites.serializers_v2 import TahoeSiteCreationSerializer
from tahoe_sites.api import add_user_to_organization

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.validators import validate_slug, ValidationError
from django.conf import settings
from django.db import transaction

from openedx.core.djangoapps.appsembler.sites.serializers import RegistrationSerializer


class Command(BaseCommand):
    """
    Create a Tahoe 2.0 demo something.localhost:18000 site for devstack.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            help='A slug for the username and used as a site name prefix e.g. something.localhost:18000',
            nargs=1,
            type=str,
        )
        parser.add_argument(
            'base-domain',
            help='The base domain set to either `localhost` or something like `devstack.tahoe`',
            nargs=1,
            type=str,
        )

    def congrats(self, **kwargs):
        """
        Write a congrats message.

        :param kwargs: congrats message format keyword arguments.
        """
        self.stdout.write(inspect.cleandoc(
            """
            Congrats, Your site is ready!

            Site URL: "http://{site}/"

            Please add the following entry to your /etc/hosts file:

                127.0.0.1 {domain}

            You can login via FusionAuth via a Learner or an Administrator depending
            on the user.data.platform_role you chose.

            Enjoy!
            """.format(**kwargs)
        ))

    def handle(self, *args, **options):
        with transaction.atomic():
            self._handle_with_atmoic(*args, **options)

    def _handle_with_atmoic(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('This only works on devstack.')

        name = options['name'][0].lower()
        base_domain = options['base-domain'][0].lower()
        try:
            validate_slug(name)
        except ValidationError:
            raise CommandError('Please enter a valid slug')

        if User.objects.filter(username=name).exists():
            raise CommandError('User exists with the username: "{}". Please choose another name.'.format(name))

        domain = '{name}.{base_domain}'.format(name=name, base_domain=base_domain)
        site_name = '{domain}:18000'.format(domain=domain)

        serializer = TahoeSiteCreationSerializer(data={
            'short_name': name,
            'domain': site_name,
        })
        if not serializer.is_valid():
            raise CommandError('Something went wrong with the process: \n{errors}'.format(
                errors=json.dumps(serializer.errors, indent=4)
            ))
        site_data = serializer.save()

        # This admin cannot login without FusionAuth, but it's added for simulation purposes
        # in testing.
        fake_admin_user = User.objects.create_user(
            username=name,
            email='{}@example.com'.format(name),
            password=name,
        )
        add_user_to_organization(
            user=fake_admin_user,
            organization=site_data['organization'],
            is_admin=True,
        )

        self.congrats(
            name=fake_admin_user.username,
            email=fake_admin_user.email,
            password=name,
            site=site_name,
            domain=domain,
        )
