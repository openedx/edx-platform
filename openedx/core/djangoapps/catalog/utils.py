"""Helper functions for working with the catalog service."""
from django.conf import settings
from django.contrib.auth import get_user_model
from edx_rest_api_client.client import EdxRestApiClient
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.lib.edx_api_utils import get_edx_api_data
from openedx.core.lib.token_utils import JwtBuilder


User = get_user_model()  # pylint: disable=invalid-name


def create_catalog_api_client(user, catalog_integration):
    """Returns an API client which can be used to make catalog API requests."""
    scopes = ['email', 'profile']
    expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
    jwt = JwtBuilder(user).build_token(scopes, expires_in)

    return EdxRestApiClient(catalog_integration.internal_api_url, jwt=jwt)


def get_programs(uuid=None, type=None):  # pylint: disable=redefined-builtin
    """Retrieve marketable programs from the catalog service.

    Keyword Arguments:
        uuid (string): UUID identifying a specific program.
        type (string): Filter programs by type (e.g., "MicroMasters" will only return MicroMasters programs).

    Returns:
        list of dict, representing programs.
        dict, if a specific program is requested.
    """
    catalog_integration = CatalogIntegration.current()
    if catalog_integration.enabled:
        try:
            user = User.objects.get(username=catalog_integration.service_username)
        except User.DoesNotExist:
            return []

        api = create_catalog_api_client(user, catalog_integration)

        cache_key = '{base}.programs{type}'.format(
            base=catalog_integration.CACHE_KEY,
            type='.' + type if type else ''
        )

        querystring = {
            'marketable': 1,
            'exclude_utm': 1,
        }
        if type:
            querystring['type'] = type

        return get_edx_api_data(
            catalog_integration,
            user,
            'programs',
            resource_id=uuid,
            cache_key=cache_key if catalog_integration.is_cache_enabled else None,
            api=api,
            querystring=querystring,
        )
    else:
        return []


def get_program_types():
    """Retrieve all program types from the catalog service.

    Returns:
        list of dict, representing program types.
    """
    catalog_integration = CatalogIntegration.current()
    if catalog_integration.enabled:
        try:
            user = User.objects.get(username=catalog_integration.service_username)
        except User.DoesNotExist:
            return []

        api = create_catalog_api_client(user, catalog_integration)
        cache_key = '{base}.program_types'.format(base=catalog_integration.CACHE_KEY)

        return get_edx_api_data(
            catalog_integration,
            user,
            'program_types',
            cache_key=cache_key if catalog_integration.is_cache_enabled else None,
            api=api
        )
    else:
        return []


def get_programs_with_type_logo():
    """
    Join program type logos with programs of corresponding type.
    """
    programs_list = get_programs()
    program_types = get_program_types()

    type_logo_map = {program_type['name']: program_type['logo_image'] for program_type in program_types}

    for program in programs_list:
        program['logo_image'] = type_logo_map[program['type']]

    return programs_list
