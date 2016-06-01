"""Helper functions to get data from APIs"""
from __future__ import unicode_literals
import logging

from django.core.cache import cache
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.lib.token_utils import get_id_token


log = logging.getLogger(__name__)


def get_edx_api_data(api_config, user, resource,
                     api=None, resource_id=None, querystring=None, cache_key=None):
    """GET data from an edX REST API.

    DRY utility for handling caching and pagination.

    Arguments:
        api_config (ConfigurationModel): The configuration model governing interaction with the API.
        user (User): The user to authenticate as when requesting data.
        resource (str): Name of the API resource being requested.

    Keyword Arguments:
        api (APIClient): API client that will use for requesting data.
        resource_id (int or str): Identifies a specific resource to be retrieved.
        querystring (dict): Optional query string parameters.
        cache_key (str): Where to cache retrieved data. The cache will be ignored if this is omitted
            (neither inspected nor updated).

    Returns:
        Data returned by the API. When hitting a list endpoint, extracts "results" (list of dict)
        returned by DRF-powered APIs.
    """
    no_data = []

    if not api_config.enabled:
        log.warning('%s configuration is disabled.', api_config.API_NAME)
        return no_data

    if cache_key:
        cache_key = '{}.{}'.format(cache_key, resource_id) if resource_id else cache_key

        cached = cache.get(cache_key)
        if cached:
            return cached

    try:
        if not api:
            jwt = get_id_token(user, api_config.OAUTH2_CLIENT_NAME)
            api = EdxRestApiClient(api_config.internal_api_url, jwt=jwt)
    except:  # pylint: disable=bare-except
        log.exception('Failed to initialize the %s API client.', api_config.API_NAME)
        return no_data

    try:
        endpoint = getattr(api, resource)
        querystring = querystring if querystring else {}
        response = endpoint(resource_id).get(**querystring)

        if resource_id:
            results = response
        else:
            results = _traverse_pagination(response, endpoint, querystring, no_data)
    except:  # pylint: disable=bare-except
        log.exception('Failed to retrieve data from the %s API.', api_config.API_NAME)
        return no_data

    if cache_key:
        cache.set(cache_key, results, api_config.cache_ttl)

    return results


def _traverse_pagination(response, endpoint, querystring, no_data):
    """Traverse a paginated API response.

    Extracts and concatenates "results" (list of dict) returned by DRF-powered APIs.
    """
    results = response.get('results', no_data)

    page = 1
    next_page = response.get('next')
    while next_page:
        page += 1
        querystring['page'] = page
        response = endpoint.get(**querystring)
        results += response.get('results', no_data)
        next_page = response.get('next')

    return results
