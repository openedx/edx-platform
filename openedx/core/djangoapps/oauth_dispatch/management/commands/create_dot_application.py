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

    def handle(self, *args, **options):
        app_name = options['name']
        username = options['username']
        grant_type = options['grant_type']
        redirect_uris = options['redirect_uris']

        user = User.objects.get(username=username)

        if Application.objects.filter(user=user, name=app_name).exists():
            logger.info('Application with name {} and user {} already exists.'.format(
                app_name,
                username
            ))
            return

        application = Application.objects.create(
            name=app_name,
            user=user,
            redirect_uris=redirect_uris,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=grant_type
        )
        application.save()
        logger.info('Created {} application with id: {}, client_id: {}, and client_secret: {}'.format(
            app_name,
            application.id,
            application.client_id,
            application.client_secret
        ))
