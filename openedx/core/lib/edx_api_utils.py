"""Helper functions to get data from APIs"""


import logging

from django.core.cache import cache

from openedx.core.lib.cache_utils import zpickle, zunpickle

log = logging.getLogger(__name__)


def get_fields(fields, response):
    """Extracts desired fields from the API response"""
    results = {}
    for field in fields:
        results[field] = response.get(field)
    return results


def get_edx_api_data(api_config, resource, api, resource_id=None, querystring=None, cache_key=None, many=True,
                     traverse_pagination=True, fields=None, long_term_cache=False):
    """GET data from an edX REST API.

    DRY utility for handling caching and pagination.

    Arguments:
        api_config (ConfigurationModel): The configuration model governing interaction with the API.
        resource (str): Name of the API resource being requested.

    Keyword Arguments:
        api (APIClient): API client to use for requesting data.
        resource_id (int or str): Identifies a specific resource to be retrieved.
        querystring (dict): Optional query string parameters.
        cache_key (str): Where to cache retrieved data. The cache will be ignored if this is omitted
            (neither inspected nor updated).
        many (bool): Whether the resource requested is a collection of objects, or a single object.
            If false, an empty dict will be returned in cases of failure rather than the default empty list.
        traverse_pagination (bool): Whether to traverse pagination or return paginated response..
        long_term_cache (bool): Whether to use the long term cache ttl or the standard cache ttl

    Returns:
        Data returned by the API. When hitting a list endpoint, extracts "results" (list of dict)
        returned by DRF-powered APIs.
    """
    no_data = [] if many else {}

    if not api_config.enabled:
        log.warning('%s configuration is disabled.', api_config.API_NAME)
        return no_data

    if cache_key:
        cache_key = '{}.{}'.format(cache_key, resource_id) if resource_id is not None else cache_key
        cache_key += '.zpickled'

        cached = cache.get(cache_key)
        if cached:
            try:
                cached_response = zunpickle(cached)
            except Exception:  # pylint: disable=broad-except
                # Data is corrupt in some way.
                log.warning("Data for cache is corrupt for cache key %s", cache_key)
                cache.delete(cache_key)
            else:
                if fields:
                    cached_response = get_fields(fields, cached_response)

                return cached_response

    try:
        endpoint = getattr(api, resource)
        querystring = querystring if querystring else {}
        response = endpoint(resource_id).get(**querystring)

        if resource_id is None and traverse_pagination:
            results = _traverse_pagination(response, endpoint, querystring, no_data)
        else:
            results = response

    except:  # pylint: disable=bare-except
        log.exception('Failed to retrieve data from the %s API.', api_config.API_NAME)
        return no_data

    if cache_key:
        zdata = zpickle(results)
        cache_ttl = api_config.cache_ttl
        if long_term_cache:
            cache_ttl = api_config.long_term_cache_ttl
        cache.set(cache_key, zdata, cache_ttl)

    if fields:
        results = get_fields(fields, results)

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
