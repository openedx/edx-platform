"""Helper functions for working with Credentials."""
from __future__ import unicode_literals
import logging

from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.programs.utils import get_programs_for_credentials
from openedx.core.lib.token_utils import get_id_token


log = logging.getLogger(__name__)


def get_user_credentials(user):
    """Given a user, get credentials earned from the Credentials service.

    Arguments:
        user (User): The user to authenticate as when requesting credentials.

    Returns:
        list of dict, representing credentials returned by the Credentials
        service.
    """
    credentials_config = CredentialsApiConfig.current()
    credentials = []
    if not credentials_config.enabled:
        log.warning('Credentials configuration is disabled.')
        return credentials

    try:
        jwt = get_id_token(user, credentials_config.OAUTH2_CLIENT_NAME)
        api = EdxRestApiClient(credentials_config.internal_api_url, jwt=jwt)
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to initialize the Credentials API client.')
        return credentials

    try:
        response = api.user_credentials.get(username=user.username)
        credentials = response.get('results')
        page = 1
        next_page = response.get('next', None)
        while next_page:
            page += 1
            response = api.user_credentials.get(page=page, username=user.username)
            credentials += response.get('results')
            next_page = response.get('next', None)

    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to retrieve credentials from the Credentials API.')
        return credentials

    return credentials


def get_user_program_credentials(user):
    """Given a user, get the list of all program credentials earned and returns
    list of dictionaries containing related programs data.

    Arguments:
        user (User): The user object for getting programs credentials.

    Returns:
        list, containing programs dictionaries.
    """
    programs_credentials_data = []
    credential_configuration = CredentialsApiConfig.current()
    if not credential_configuration.is_learner_issuance_enabled:
        log.debug('Display of certificates for programs is disabled.')
        return programs_credentials_data

    credentials = get_user_credentials(user)
    if not credentials:
        log.info('No credential earned by the given user.')
        return programs_credentials_data

    programs_credentials = []
    for credential in credentials:
        try:
            if 'program_id' in credential['credential'] and credential['status'] == 'awarded':
                programs_credentials.append(credential)
        except KeyError:
            log.exception('Invalid credential structure: %r', credential)

    if programs_credentials:
        programs_credentials_data = get_programs_for_credentials(user, programs_credentials)

    return programs_credentials_data
