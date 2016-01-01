"""Helper functions to get data from APIs"""
from __future__ import unicode_literals
import logging

from django.core.cache import cache
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.lib.token_utils import get_id_token


log = logging.getLogger(__name__)


def get_edx_api_data(api_config, user, resource, querystring=None, cache_key=None):
    """Fetch data from an API using provided API configuration and resource
        name.

    Arguments:
        api_config (ConfigurationModel): The configuration model governing
            interaction with the API.
        user (User): The user to authenticate as when requesting data.
        resource(str): Name of the API resource for which data is being
            requested.
        querystring(dict): Querystring parameters that might be required to
            request data.
        cache_key(str): Where to cache retrieved data. Omitting this will cause the
            cache to be bypassed.

    Returns:
        list of dict, representing data returned by the API.
    """
    no_data = []

    if not api_config.enabled:
        log.warning('%s configuration is disabled.', api_config.API_NAME)
        return no_data

    if cache_key:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    try:
        jwt = get_id_token(user, api_config.OAUTH2_CLIENT_NAME)
        api = EdxRestApiClient(api_config.internal_api_url, jwt=jwt)
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to initialize the %s API client.', api_config.API_NAME)
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
        log.exception('Failed to retrieve data from the %s API.', api_config.API_NAME)
        return no_data

    if cache_key:
        cache.set(cache_key, results, api_config.cache_ttl)

    return results
