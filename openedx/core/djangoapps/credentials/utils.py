"""Helper functions for working with Credentials."""


from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.lib.edx_api_utils import get_edx_api_data


def get_credentials_records_url(program_uuid=None):
    """
    Returns a URL for a given records page (or general records list if given no UUID).
    May return None if this feature is disabled.

    Arguments:
        program_uuid (str): Optional program uuid to link for a program records URL
    """
    base_url = CredentialsApiConfig.current().public_records_url
    if base_url is None:
        return None
    if program_uuid:
        # Credentials expects the uuid without dashes so we are converting here
        return base_url + 'programs/{}/'.format(program_uuid.replace('-', ''))
    return base_url


def get_credentials_api_client(user, org=None):
    """
    Returns an authenticated Credentials API client.

    Arguments:
        user (User): The user to authenticate as when requesting credentials.
        org (str): Optional organization to look up the site config for, rather than the current request

    """
    jwt = create_jwt_for_user(user)

    if org is None:
        url = CredentialsApiConfig.current().internal_api_url  # by current request
    else:
        url = CredentialsApiConfig.get_internal_api_url_for_org(org)  # by org
    return EdxRestApiClient(url, jwt=jwt)


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
    cache_key = '{}.{}'.format(credential_configuration.CACHE_KEY, user.username) if use_cache else None
    if cache_key and program_uuid:
        cache_key = '{}.{}'.format(cache_key, program_uuid)
    api = get_credentials_api_client(user)

    return get_edx_api_data(
        credential_configuration, 'credentials', api=api, querystring=querystring, cache_key=cache_key
    )
