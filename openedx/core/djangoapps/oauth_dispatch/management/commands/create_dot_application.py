"""
Management command for creating a Django OAuth Toolkit Application model.
"""

from __future__ import unicode_literals

import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from oauth2_provider.models import get_application_model

logger = logging.getLogger(__name__)

Application = get_application_model()


class Command(BaseCommand):
    """
    Creates a Django OAuth Toolkit (DOT) Application Instance.
    """
    help = "Creates a Django OAuth Toolkit (DOT) Application Instance."

    def add_arguments(self, parser):
        grant_type_choices = [grant_type[0] for grant_type in Application.GRANT_TYPES]
        parser.add_argument('name',
                            action='store',
                            help='The name of this DOT Application')
        parser.add_argument('username',
                            action='store',
                            help='The name of the LMS user associated with this DOT Application')
        parser.add_argument('--grant-type',
                            action='store',
                            dest='grant_type',
                            default=Application.GRANT_CLIENT_CREDENTIALS,
                            choices=grant_type_choices,
                            help='The type of authorization this application can grant')
        parser.add_argument('--redirect-uris',
                            action='store',
                            dest='redirect_uris',
                            default='',
                            help='The redirect URI(s) for this application.  Multiple URIs should be space separated.')
        parser.add_argument('--public',
                            action='store_true',
                            dest='public',
                            default=False,
                            help='Make the application public?  Confidential by default.')
        parser.add_argument('--client-id',
                            action='store',
                            dest='client_id',
                            default='',
                            help='The client_id for this application. If omitted, one will be generated.')
        parser.add_argument('--client-secret',
                            action='store',
                            dest='client_secret',
                            default='',
                            help='The client_secret for this application. If omitted, one will be generated.')

    def handle(self, *args, **options):
        app_name = options['name']
        username = options['username']
        grant_type = options['grant_type']
        redirect_uris = options['redirect_uris']
        client_type = Application.CLIENT_PUBLIC if options['public'] else Application.CLIENT_CONFIDENTIAL
        client_id = options['client_id']
        client_secret = options['client_secret']

        user = User.objects.get(username=username)

        if Application.objects.filter(user=user, name=app_name).exists():
            logger.info('Application with name {} and user {} already exists.'.format(
                app_name,
                username
            ))
            return

        create_kwargs = dict(
            name=app_name,
            user=user,
            redirect_uris=redirect_uris,
            client_type=client_type,
            authorization_grant_type=grant_type
        )
        if client_id:
            create_kwargs['client_id'] = client_id
        if client_secret:
            create_kwargs['client_secret'] = client_secret

        application = Application.objects.create(**create_kwargs)
        application.save()
        logger.info('Created {} application with id: {}, client_id: {}, and client_secret: {}'.format(
            app_name,
            application.id,
            application.client_id,
            application.client_secret
        ))
