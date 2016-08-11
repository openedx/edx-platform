"""Helper functions for working with the catalog service."""
import abc
import logging

from django.conf import settings
from django.core.cache import cache
from edx_rest_api_client.client import EdxRestApiClient
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.lib.edx_api_utils import get_edx_api_data
from openedx.core.lib.token_utils import JwtBuilder


log = logging.getLogger(__name__)


def create_catalog_api_client(user, catalog_integration):
    """Returns an API client which can be used to make catalog API requests."""
    scopes = ['email', 'profile']
    expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
    jwt = JwtBuilder(user).build_token(scopes, expires_in)

    return EdxRestApiClient(catalog_integration.internal_api_url, jwt=jwt)


def get_programs(user, uuid=None, type=None):  # pylint: disable=redefined-builtin
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
        api = create_catalog_api_client(user, catalog_integration)

        cache_key = '{base}.programs{type}'.format(
            base=catalog_integration.CACHE_KEY,
            type='.' + type if type else ''
        )

        querystring = {
            'marketable': 1,
            'exclude_utm': 1,
            'published_course_runs_only': 1,
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


def munge_catalog_program(catalog_program):
    """Make a program from the catalog service look like it came from the programs service.

    Catalog-based MicroMasters need to be displayed in the LMS. However, the LMS
    currently retrieves all program data from the soon-to-be-retired programs service.
    Consuming program data exclusively from the catalog service would have taken more time
    than we had prior to the MicroMasters launch. This is a functional middle ground
    introduced by ECOM-5460. Cleaning up this debt is tracked by ECOM-4418.

    Arguments:
        catalog_program (dict): The catalog service's representation of a program.

    Return:
        dict, imitating the schema used by the programs service.
    """
    return {
        'id': catalog_program['uuid'],
        'name': catalog_program['title'],
        'subtitle': catalog_program['subtitle'],
        'category': catalog_program['type'],
        'marketing_slug': catalog_program['marketing_slug'],
        'organizations': [
            {
                'display_name': organization['name'],
                'key': organization['key']
            } for organization in catalog_program['authoring_organizations']
        ],
        'course_codes': [
            {
                'display_name': course['title'],
                'key': course['key'],
                'organization': {
                    # The Programs schema only supports one organization here.
                    'display_name': course['owners'][0]['name'],
                    'key': course['owners'][0]['key']
                },
                'run_modes': [
                    {
                        'course_key': run['key'],
                        'run_key': CourseKey.from_string(run['key']).run,
                        'mode_slug': 'verified'
                    } for run in course['course_runs']
                ],
            } for course in catalog_program['courses']
        ],
        'banner_image_urls': {
            'w1440h480': catalog_program['banner_image']['large']['url'],
            'w726h242': catalog_program['banner_image']['medium']['url'],
            'w435h145': catalog_program['banner_image']['small']['url'],
            'w348h116': catalog_program['banner_image']['x-small']['url'],
        },
    }


def get_and_cache_course_runs(course_keys, user):
    """
    Get course run's data from the course catalog service and cache it.
    """
    catalog_course_runs_against_course_keys = {}
    catalog_integration = CatalogIntegration.current()
    if catalog_integration.enabled:
        api = create_catalog_api_client(user, catalog_integration)

        catalog_data = get_edx_api_data(
            catalog_integration,
            user,
            'course_runs',
            api=api,
            querystring={'keys': ",".join(course_keys), 'exclude_utm': 1},
        )
        if catalog_data:
            for catalog_course_run in catalog_data:
                CatalogCacheUtility.cache_course_run(catalog_course_run)
                catalog_course_runs_against_course_keys[catalog_course_run["key"]] = catalog_course_run
    return catalog_course_runs_against_course_keys


def get_course_runs(course_keys, user):
    """
    Get course run data from the course catalog service if not available in cache.

    Arguments:
        course_keys ([CourseKey]): A list of Course key object identifying the run whose data we want.
        user (User): The user to authenticate as when making requests to the catalog service.

    Returns:
        dict of catalog course runs against course keys, empty if no data could be retrieved.
    """
    catalog_course_runs_against_course_keys = CatalogCacheUtility.get_cached_catalog_course_runs(
        course_keys
    )
    if len(catalog_course_runs_against_course_keys.keys()) != len(course_keys):
        missing_course_keys = CatalogCacheUtility.get_course_keys_not_found_in_cache(
            course_keys, catalog_course_runs_against_course_keys.keys()
        )
        catalog_course_runs_against_course_keys.update(
            get_and_cache_course_runs(missing_course_keys, user)
        )

    return catalog_course_runs_against_course_keys


def get_run_marketing_url(course_key, user):
    """
    Get a course run's marketing URL from the course catalog service.

    Arguments:
        course_key (CourseKey): Course key object identifying the run whose marketing URL we want.
        user (User): The user to authenticate as when making requests to the catalog service.

    Returns:
        string, the marketing URL, or None if no URL is available.
    """
    course_marketing_urls = get_run_marketing_urls([course_key], user)
    return course_marketing_urls.get(unicode(course_key))


def get_run_marketing_urls(course_keys, user):
    """
    Get course run marketing URLs from the course catalog service against course keys.

    Arguments:
        course_keys ([CourseKey]): A list of Course key object identifying the run whose data we want.
        user (User): The user to authenticate as when making requests to the catalog service.

    Returns:
        dict of run marketing URLs against course keys
    """
    course_marketing_urls = {}
    course_catalog_dict = get_course_runs(course_keys, user)
    if not course_catalog_dict:
        return course_marketing_urls

    for course_key in course_keys:
        course_key_string = unicode(course_key)
        if course_key_string in course_catalog_dict:
            course_marketing_urls[course_key_string] = course_catalog_dict[course_key_string].get('marketing_url')

    return course_marketing_urls


class CatalogCacheUtility(object):
    """
    Non-instantiatable class housing utility methods for caching catalog API data.
    """
    __metaclass__ = abc.ABCMeta
    CACHE_KEY_PREFIX = "catalog.course_runs."

    @classmethod
    def get_course_keys_not_found_in_cache(cls, course_keys, cached_course_run_keys):
        """
        Get course key strings for which course run data is not available in cache.

        Arguments:
            course_key (CourseKey): CourseKey object to create corresponding catalog cache key.

        Returns:
            list of string rep of course keys not found in catalog cache.
        """
        missing_course_keys = []
        for course_key in course_keys:
            course_key_string = unicode(course_key)
            if course_key_string not in cached_course_run_keys:
                missing_course_keys.append(course_key_string)

        log.info("Cached catalog course run data missing for: '{}'".format(
            ", ".join(missing_course_keys)
        ))
        return missing_course_keys

    @classmethod
    def get_cached_catalog_course_runs(cls, course_keys):
        """
        Get course runs from cache against course keys.

        Arguments:
            course_keys ([CourseKey]): List of CourseKey object identifying the run whose data we want.

        Returns:
            dict of catalog course run against course key string
        """
        course_catalog_run_cache_keys = [
            cls._get_cache_key_name(course_key)
            for course_key in course_keys
        ]
        cached_catalog_course_runs = cache.get_many(course_catalog_run_cache_keys)
        return {
            cls._extract_course_key_from_cache_key_name(cached_key): cached_course_run
            for cached_key, cached_course_run in cached_catalog_course_runs.iteritems()
        }

    @classmethod
    def cache_course_run(cls, catalog_course_run):
        """
        Caches catalog course run for course key.
        """
        cache.set(
            cls._get_cache_key_name(catalog_course_run["key"]),
            catalog_course_run,
            CatalogIntegration.current().cache_ttl
        )

    @classmethod
    def _get_cache_key_name(cls, course_key):
        """
        Returns key name to use to cache catalog course run data for course key.

        Arguments:
            course_key (CourseKey): CourseKey object to create corresponding catalog cache key.

        Returns:
            string, catalog cache key against course key.
        """
        return "{}{}".format(cls.CACHE_KEY_PREFIX, unicode(course_key))

    @classmethod
    def _extract_course_key_from_cache_key_name(cls, catalog_course_run_cache_key):
        """
        Returns course_key extracted from cache key of catalog course run data.
        """
        return catalog_course_run_cache_key.replace(cls.CACHE_KEY_PREFIX, '')
