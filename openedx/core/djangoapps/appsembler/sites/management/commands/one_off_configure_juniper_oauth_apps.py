from oauth2_provider.generators import generate_client_secret
from oauth2_provider.models import Application

from django.conf import settings
from django.core.management import BaseCommand, call_command

from openedx.core.djangoapps.appsembler.auth.models import TrustedApplication


class Command(BaseCommand):
    # TODO: Remove after the Juniper cut-over is complete
    help = "One off command: configures the OAuth Application entries with proper settings after the Juniper cut-over."

    def handle(self, *args, **options):
        # Create the Login Service for JWT a new Juniper thing
        call_command(
            'create_dot_application',
            'Login Service for JWT Cookies',
            'login_service_user',  # Matches the user created via the `migrate-edx-cluster/migrate_mysql.yml` playbook
            grant_type='password',
            redirect_uris='',
            client_id='login-service-client-id',
            client_secret=generate_client_secret(),
            public=True,
            update=True,
        )

        # Create the AMC Django OAuth Toolkit application. It was called Client in Hawthorn.
        call_command(
            'create_dot_application',
            'AMC',
            'amc_service_user',  # Matches the user created via the `migrate-edx-cluster/migrate_mysql.yml` playbook
            grant_type='password',
            redirect_uris='{}/complete/edx-oidc/'.format(settings.AMC_APP_URL),
            client_id=settings.AMC_APP_OAUTH2_CLIENT_ID,
            client_secret=settings.ENV_TOKENS['TEMP_AMC_APP_OAUTH2_CLIENT_SECRET'],
            public=False,
            skip_authorization=True,
            update=True,
        )

        # Mark the AMC as TrustedApplication to avoid losing tokens during password reset.
        TrustedApplication.objects.get_or_create(
            application=Application.objects.get(client_id=settings.AMC_APP_OAUTH2_CLIENT_ID)
        )
