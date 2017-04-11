"""Helper functions for working with the catalog service."""
import copy
import logging

import waffle
from django.conf import settings
from django.contrib.auth import get_user_model
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.lib.edx_api_utils import get_edx_api_data
from openedx.core.lib.token_utils import JwtBuilder


log = logging.getLogger(__name__)

User = get_user_model()  # pylint: disable=invalid-name


def create_catalog_api_client(user, catalog_integration):
    """Returns an API client which can be used to make catalog API requests."""
    scopes = ['email', 'profile']
    expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
    jwt = JwtBuilder(user).build_token(scopes, expires_in)

    return EdxRestApiClient(catalog_integration.internal_api_url, jwt=jwt)


def get_programs(uuid=None, types=None):  # pylint: disable=redefined-builtin
    """Retrieve marketable programs from the catalog service.

    Keyword Arguments:
        uuid (string): UUID identifying a specific program.
        types (list of string): List of program type names used to filter programs by type
                                (e.g., ["MicroMasters"] will only return MicroMasters programs,
                                ["MicroMasters", "XSeries"] will return MicroMasters and XSeries programs).

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
        types_param = ','.join(types) if types else None

        cache_key = '{base}.programs{types}'.format(
            base=catalog_integration.CACHE_KEY,
            types='.' + types_param if types_param else ''
        )

        querystring = {
            'exclude_utm': 1,
            'status': ('active', 'retired',),
        }

        if uuid:
            querystring['use_full_course_serializer'] = 1

        if types_param:
            querystring['types'] = types_param

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


def get_program_types(name=None):
    """Retrieve program types from the catalog service.

    Keyword Arguments:
        name (string): Name identifying a specific program.

    Returns:
        list of dict, representing program types.
        dict, if a specific program type is requested.
    """
    catalog_integration = CatalogIntegration.current()
    if catalog_integration.enabled:
        try:
            user = User.objects.get(username=catalog_integration.service_username)
        except User.DoesNotExist:
            return []

        api = create_catalog_api_client(user, catalog_integration)
        cache_key = '{base}.program_types'.format(base=catalog_integration.CACHE_KEY)

        data = get_edx_api_data(
            catalog_integration,
            user,
            'program_types',
            cache_key=cache_key if catalog_integration.is_cache_enabled else None,
            api=api
        )

        # Filter by name if a name was provided
        if name:
            data = next(program_type for program_type in data if program_type['name'] == name)

        return data
    else:
        return []


def get_programs_with_type(types=None):
    """
    Return the list of programs. You can filter the types of programs returned using the optional
    types parameter. If no filter is provided, all programs of all types will be returned.

    The program dict is updated with the fully serialized program type.

    Keyword Arguments:
        types (list): List of program type slugs to filter by.

    Return:
        list of dict, representing the active programs.
    """
    programs_with_type = []
    programs = get_programs(types=types)

    if programs:
        program_types = {program_type['name']: program_type for program_type in get_program_types()}
        for program in programs:
            # deepcopy the program dict here so we are not adding
            # the type to the cached object
            program_with_type = copy.deepcopy(program)
            program_with_type['type'] = program_types[program['type']]
            programs_with_type.append(program_with_type)

    return programs_with_type


def get_course_runs():
    """
    Retrieve all the course runs from the catalog service.

    Returns:
        list of dict with each record representing a course run.
    """
    catalog_integration = CatalogIntegration.current()
    course_runs = []
    if catalog_integration.enabled:
        try:
            user = User.objects.get(username=catalog_integration.service_username)
        except User.DoesNotExist:
            log.error(
                'Catalog service user with username [%s] does not exist. Course runs will not be retrieved.',
                catalog_integration.service_username,
            )
            return course_runs

        api = create_catalog_api_client(user, catalog_integration)

        querystring = {
            'page_size': catalog_integration.page_size,
            'exclude_utm': 1,
        }

        course_runs = get_edx_api_data(
            catalog_integration,
            user,
            'course_runs',
            api=api,
            querystring=querystring,
        )

    return course_runs
