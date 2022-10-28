"""Helper functions for working with Credentials."""
import requests
from edx_rest_api_client.auth import SuppliedJwtAuth

from django.conf import settings

from openedx.core.djangoapps.credentials.config import USE_LEARNER_RECORD_MFE
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.lib.edx_api_utils import get_api_data


def get_credentials_records_url(program_uuid=None):
    """
    Returns a URL for a given records page (or general records list if given no UUID).
    May return None if this feature is disabled.

    Arguments:
        program_uuid (str): Optional program uuid to link for a program records URL
    """
    base_url = settings.CREDENTIALS_PUBLIC_SERVICE_URL
    learner_record_mfe_base_url = settings.LEARNER_RECORD_MICROFRONTEND_URL
    use_learner_record_mfe = USE_LEARNER_RECORD_MFE.is_enabled() and learner_record_mfe_base_url

    if not base_url and not use_learner_record_mfe:
        return None

    # If we have a program uuid we build a link to the appropriate Program Record page in Credentials (or the Learner
    # Record MFE)
    if program_uuid:
        # Credentials expects the UUID without dashes so we strip them here
        stripped_program_uuid = program_uuid.replace('-', '')
        if use_learner_record_mfe:
            return f"{learner_record_mfe_base_url}/{stripped_program_uuid}/"
        return f"{base_url}/records/programs/{stripped_program_uuid}/"
    else:
        # Otherwise, build a link to the appropriate Learner Record index page
        if use_learner_record_mfe:
            return f"{learner_record_mfe_base_url}/"
        else:
            return f"{base_url}/records/"


def get_credentials_api_client(user):
    """
    Returns an authenticated Credentials API client.

    Arguments:
        user (User): The user to authenticate as when requesting credentials.
    """
    scopes = ['email', 'profile', 'user_id']
    jwt = create_jwt_for_user(user, scopes=scopes)

    client = requests.Session()
    client.auth = SuppliedJwtAuth(jwt)
    return client


def get_credentials_api_base_url(org=None):
    """
    Returns a credentials API base URL.

    Arguments:
        org (str): Optional organization to look up the site config for, rather than the current request
    """
    if org is None:
        url = CredentialsApiConfig.current().internal_api_url  # by current request
    else:
        url = CredentialsApiConfig.get_internal_api_url_for_org(org)  # by org

    return url


def get_credentials(user, program_uuid=None, credential_type=None):
    """
    Given a user, get credentials earned from the credentials service.

    Arguments:
        user (User): The user to authenticate as when requesting credentials.

    Keyword Arguments:
        program_uuid (str): UUID of the program whose credential to retrieve.
        credential_type (str): Which type of credentials to return (course-run or program)

    Returns:
        list of dict, representing credentials returned by the Credentials
        service.
    """
    credential_configuration = CredentialsApiConfig.current()

    querystring = {'username': user.username, 'status': 'awarded', 'only_visible': 'True'}

    if program_uuid:
        querystring['program_uuid'] = program_uuid

    if credential_type:
        querystring['type'] = credential_type

    # Bypass caching for staff users, who may be generating credentials and
    # want to see them displayed immediately.
    use_cache = credential_configuration.is_cache_enabled and not user.is_staff
    cache_key = f'{credential_configuration.CACHE_KEY}.{user.username}' if use_cache else None
    if cache_key and program_uuid:
        cache_key = f'{cache_key}.{program_uuid}'

    api_client = get_credentials_api_client(user)
    base_api_url = get_credentials_api_base_url()

    return get_api_data(
        credential_configuration,
        'credentials',
        api_client=api_client,
        base_api_url=base_api_url,
        querystring=querystring,
        cache_key=cache_key
    )
