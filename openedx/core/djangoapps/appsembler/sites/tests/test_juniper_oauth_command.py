import pytest

from django.core.management import call_command
from oauth2_provider.models import Application


@pytest.mark.django_db
def test_one_off_configure_juniper_oauth_apps(settings):
    """
    Test the `./manage.py lms one_off_configure_juniper_oauth_apps` command.
    """
    settings.AMC_APP_OAUTH2_CLIENT_ID = 'amc-app-id'
    settings.ENV_TOKENS = {
        'TEMP_AMC_APP_OAUTH2_CLIENT_SECRET': 'amc-app-secret',
    }
    # Create needed users
    call_command('manage_user', 'amc_service_user', 'amc@test', is_staff=True)
    call_command('manage_user', 'login_service_user', 'amc@test', is_staff=True)

    # Test if the command works
    call_command('one_off_configure_juniper_oauth_apps')

    assert Application.objects.get(name='AMC'), 'Ensure AMC app exists'
    assert Application.objects.get(client_id='login-service-client-id'), 'Ensure JWT login app exists'
    assert Application.objects.get(name='AMC').trustedapplication, \
        'AMC tokens must not be deleted on password reset'
