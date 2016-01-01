"""Helper functions to get data from APIs"""
from __future__ import unicode_literals
import logging

from django.core.cache import cache
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.lib.token_utils import get_id_token


log = logging.getLogger(__name__)


def get_api_data(api_config, user, api_name, resource, querystring=None, use_cache=False, cache_key=None):
    """Fetch the data from the API using provided API Configuration and
    resource.

    Arguments:
        api_config: The configuration which will be user for requesting data.
        user (User): The user to authenticate as when requesting data.
        api_name: Name fo the api to be use for logging.
        resource: API resource to from where data will be requested.
        querystring: Querystring parameters that might be required to request
            data.
        use_cache: Will be used to decide whether to cache the response data
            or not.
        cache_key: cache key to be used to save response data.

    Returns:
        list of dict, representing data returned by the API.
    """
    no_data = []

    if not api_config.enabled:
        log.warning('%s configuration is disabled.', api_name)
        return no_data

    if use_cache:
        if cache_key:
            cached = cache.get(api_config.CACHE_KEY)
            if cached is not None:
                return cached
        else:
            log.warning('Cache key does not provided to cache data.')
            return no_data

    try:
        jwt = get_id_token(user, api_config.OAUTH2_CLIENT_NAME)
        api = EdxRestApiClient(api_config.internal_api_url, jwt=jwt)
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to initialize the %s API client.', api_name)
        return no_data

    try:
        querystring = {} if not querystring else querystring
        response = getattr(api, resource).get(**querystring)
        results = response.get('results', no_data)
        page = 1
        next_page = response.get('next', None)
        while next_page:
            page += 1
            querystring['page'] = page
            response = getattr(api, resource).get(**querystring)
            results += response.get('results', no_data)
            next_page = response.get('next', None)
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to retrieve data from the %s API.', api_name)
        return no_data

    if use_cache:
        cache.set(api_config.CACHE_KEY, results, api_config.cache_ttl)

    return results
