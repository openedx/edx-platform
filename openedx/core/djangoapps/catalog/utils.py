"""Helper functions for working with the catalog service."""
from urlparse import urlparse

from django.conf import settings
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.lib.edx_api_utils import get_edx_api_data
from openedx.core.lib.token_utils import JwtBuilder


def get_course_run(course_key, user):
    """Get a course run's data from the course catalog service.

    Arguments:
        course_key (CourseKey): Course key object identifying the run whose data we want.
        user (User): The user to authenticate as when making requests to the catalog service.

    Returns:
        dict, empty if no data could be retrieved.
    """
    catalog_integration = CatalogIntegration.current()

    if catalog_integration.enabled:
        scopes = ['email', 'profile']
        expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
        jwt = JwtBuilder(user).build_token(scopes, expires_in)
        api = EdxRestApiClient(catalog_integration.internal_api_url, jwt=jwt)

        data = get_edx_api_data(
            catalog_integration,
            user,
            'course_runs',
            resource_id=unicode(course_key),
            cache_key=catalog_integration.CACHE_KEY if catalog_integration.is_cache_enabled else None,
            api=api,
        )

        return data if data else {}
    else:
        return {}


def get_run_marketing_url(course_key, user):
    """Get a course run's marketing URL from the course catalog service.

    Arguments:
        course_key (CourseKey): Course key object identifying the run whose marketing URL we want.
        user (User): The user to authenticate as when making requests to the catalog service.

    Returns:
        string, the marketing URL, or None if no URL is available.
    """
    course_run = get_course_run(course_key, user)
    marketing_url = course_run.get('marketing_url')

    if marketing_url:
        # This URL may include unwanted UTM parameters in the querystring.
        # For more, see https://en.wikipedia.org/wiki/UTM_parameters.
        return strip_querystring(marketing_url)
    else:
        return None


def strip_querystring(url):
    """Strip the querystring from the provided URL.

    urlparse's ParseResult is a subclass of namedtuple. _replace is part of namedtuple's
    public API: https://docs.python.org/2/library/collections.html#collections.somenamedtuple._replace.
    The name starts with an underscore to prevent conflicts with field names.
    """
    return urlparse(url)._replace(query='').geturl()  # pylint: disable=no-member
