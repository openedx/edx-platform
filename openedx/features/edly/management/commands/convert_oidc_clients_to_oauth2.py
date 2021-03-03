"""
Edly's management command to convert OIDC clients to Django OAuth Toolkit Application clients.
"""

import logging

from django.core.management.base import BaseCommand
from oauth2_provider.models import get_application_model
from provider.oauth2.models import Client

from openedx.core.djangoapps.oauth_dispatch.models import ApplicationAccess

logger = logging.getLogger(__name__)

Application = get_application_model()


class Command(BaseCommand):
    """
    Converts OIDC clients to a Django OAuth Toolkit (DOT) Application clients.
    """
    help = "Converts OIDC clients to a Django OAuth Toolkit (DOT) Application clients."

    def _get_oidc_clients(self):
        """
        Returns current OIDC clients.
        """
        return Client.objects.all()

    def _create_or_update_application(self, user, app_name, application_kwargs):
        """
        Creates a new application if it does not exists otherwise update existing application.
        """
        application, is_created = Application.objects.update_or_create(
            user=user, name=app_name, defaults=application_kwargs
        )
        logger.info('{} {} application with id: {}, client_id: {}'.format(
            'Created' if is_created else 'Updated',
            app_name,
            application.id,
            application.client_id,
        ))
        return application

    def _create_or_update_access(self, application, application_access_kwargs):
        """
        Create application access scopes if it does not exists otherwise update existing access.
        """
        __, is_created = ApplicationAccess.objects.update_or_create(
            application_id=application.id,
            defaults=application_access_kwargs,
        )
        logger.info('{} access for {} application with scopes {}'.format(
            'Created' if is_created else 'Updated',
            application.name,
            application_access_kwargs['scopes'],
        ))

    def handle(self, *args, **options):
        application_access_kwargs = dict(
            scopes='user_id'
        )
        for client in self._get_oidc_clients():
            application_kwargs = dict(
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
                skip_authorization=True,
            )
            redirect_url = client.redirect_uri.replace('oidc', 'oauth2')
            application_kwargs['redirect_uris'] = redirect_url
            application_kwargs['client_id'] = client.client_id
            application_kwargs['client_secret'] = client.client_secret
            application = self._create_or_update_application(client.user, client.name, application_kwargs)
            app_name = '{}-backend-service'.format(client.name)
            del application_kwargs['redirect_uris']
            del application_kwargs['client_id']
            application_kwargs['authorization_grant_type'] = Application.GRANT_CLIENT_CREDENTIALS
            application_kwargs['skip_authorization'] = False
            self._create_or_update_application(client.user, app_name, application_kwargs)
            self._create_or_update_access(application, application_access_kwargs)
