"""
APIs providing support for Journals functionality.
"""
import logging
import hashlib
from urlparse import urlsplit, urlunsplit
import six

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from edx_rest_api_client.client import EdxRestApiClient
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.token_utils import JwtBuilder
from slumber.exceptions import HttpClientError, HttpServerError


LOGGER = logging.getLogger("edx.journals")
JOURNALS_CACHE_TIMEOUT = 3600  # Value is in seconds
JOURNALS_API_PATH = '/journal/api/v1/'
JOURNAL_WORKER_USERNAME = 'journals_worker'
User = get_user_model()


class DiscoveryApiClient(object):
    """
    Class for interacting with the discovery service journals endpoint
    """
    def __init__(self):
        """
        Initialize an authenticated Discovery service API client by using the
        provided user.
        """
        catalog_integration = CatalogIntegration.current()

        # Client can't be used if there is no catalog integration
        if not (catalog_integration and catalog_integration.enabled):
            LOGGER.info("Unable to create DiscoveryApiClient because catalog integration not set up or enabled")
            return None

        try:
            user = catalog_integration.get_service_user()
        except ObjectDoesNotExist:
            LOGGER.info("Unable to retrieve catalog integration service user")
            return None

        jwt = JwtBuilder(user).build_token([])
        url = configuration_helpers.get_value('COURSE_CATALOG_API_URL', settings.COURSE_CATALOG_API_URL)
        self.client = EdxRestApiClient(self.create_journals_url(url), jwt=jwt)


    def create_journals_url(self, url):
        '''rewrite the discovery url to point to journals endpoint'''
        split_url = urlsplit(url)
        override_url = urlunsplit((
            split_url.scheme,
            split_url.netloc,
            JOURNALS_API_PATH,
            split_url.query,
            split_url.fragment,
        ))
        return override_url

    def get_journals(self, orgs):
        '''get_journals from discovery, filter on orgs is supplied'''
        try:
            if orgs:
                response = self.client.journals.get(orgs=orgs, status='active')
            else:
                response = self.client.journals.get(status='active')
            LOGGER.debug('response is type=%s', type(response))
            return response.get('results')
        except (HttpClientError, HttpServerError) as err:
            LOGGER.exception(
                'Failed to get journals from discovery-service [%s]',
                err.content
            )
            return []

    def get_journal_bundles(self, uuid=''):
        try:
            response = self.client.journal_bundles(uuid).get()
        except (HttpClientError, HttpServerError) as err:
            LOGGER.exception(
                'Failed to get journal bundles from discovery-service [%s]',
                err.content
            )
            return []
        return response if uuid else response.get('results')


class JournalsApiClient(object):
    """
    Class for interacting with the Journals Service
    """
    def __init__(self):
        """
        Initialize an authenticated Journals service API client by using the
        provided user.
        """
        self.user = self.get_journals_worker()
        jwt = JwtBuilder(self.user).build_token(['email', 'profile'], 16000)
        self.client = EdxRestApiClient(
            configuration_helpers.get_value('JOURNALS_API_URL', settings.JOURNALS_API_URL),
            jwt=jwt
        )

    def get_journals_worker(self):
        """ Return journals worker """
        return User.objects.get(username=JOURNAL_WORKER_USERNAME)


def fetch_journal_access(site, user):
    """
    Retrieve journal access record for given user.
    Retrieve if from the cache if present, otherwise send GET request to the journal access api
        and store it in the cache

    Args:
        site (Site)
        user (username | str): user to retrieve access records for

    Returns:
        list of dicts: list of journal access dicts

    Raises:
        ConnectionError: raised if lms is unable to connect to the journals service.
        SlumberBaseException: raised if API response contains http error status like 4xx, 5xx etc...
        Timeout: raised if API is talking to long to respond
    """
    # TODO: WL-1560: (see jira for more info)

    # api_resourse = 'journal_access'
    # cache_key = get_cache_key(
    #     site_domain=site.domain,
    #     resourse=api_resourse,
    #     user=user
    # )
    #
    # journal_access_records = cache.get(cache_key)
    # if not journal_access_records:
    #     journal_access_records = JournalsApiClient().client.journalaccess.get(user=user)
    #     cache.set(cache_key, journal_access_records, JOURNALS_CACHE_TIMEOUT)

    journal_access_records = JournalsApiClient().client.journalaccess.get(
        user=user,
        get_latest=True
    )

    return journal_access_records


def get_cache_key(**kwargs):
    """
    Get MD5 encoded cache key for given arguments.

    Here is the format of key before MD5 encryption.
        key1:value1__key2:value2 ...

    Example:
        >>> get_cache_key(site_domain="example.com", resource="enterprise-learner")
        # Here is key format for above call
        # "site_domain:example.com__resource:enterprise-learner"
        a54349175618ff1659dee0978e3149ca

    Arguments:
        **kwargs: Key word arguments that need to be present in cache key.

    Returns:
         An MD5 encoded key uniquely identified by the key word arguments.
    """
    key = '__'.join(['{}:{}'.format(item, value) for item, value in six.iteritems(kwargs)])

    return hashlib.md5(key).hexdigest()


def journals_enabled():
    """
    Determines whether the Journals app is installed and enabled
    """
    return 'openedx.features.journals.apps.JournalsConfig' \
        in settings.INSTALLED_APPS and settings.FEATURES.get('ENABLE_JOURNAL_INTEGRATION', False)


def get_journals(site):
    """Retrieve journals from the discovery service.

    Keyword Arguments:
        site (Site): Site object for the request
        will be returned

    Returns:
        list of dict, representing journals
    """
    if not journals_enabled():
        return []

    api_resource = 'journals'
    orgs = configuration_helpers.get_current_site_orgs()

    cache_key = get_cache_key(
        site_domain=site.domain,
        resource=api_resource,
        orgs=orgs
    )

    # look up in cache
    journals = cache.get(cache_key)

    if not journals:
        api_client = DiscoveryApiClient()
        if not api_client:
            return []
        journals = api_client.get_journals(orgs)
        cache.set(cache_key, journals, JOURNALS_CACHE_TIMEOUT)

    return journals

def fix_course_images(bundle):
    """
        Set the image for a course. If the course has an image, use that. Otherwise use the first
        course run that has an image.
    """
    for course in bundle['courses']:
        course_image = course['image'].get('src') if course.get('image') else None
        if course_image:
            # Course already had image and we don't need to check course runs
            continue
        for course_run in course['course_runs']:
            if course_run['image']:
                course['image'] = course_run['image']
                break

def get_journal_bundles(site, bundle_uuid=''):
    """Retrieve journal bundles from the discovery service.

    Returns:
        list of dict, representing journal bundles
    """
    if not journals_enabled():
        return []

    api_resource = 'journal_bundles'

    cache_key = get_cache_key(
        site_domain=site.domain,
        resource=api_resource,
        bundle_uuid=bundle_uuid
    )

    journal_bundles = cache.get(cache_key)

    if not journal_bundles:
        api_client = DiscoveryApiClient()
        if not api_client:
            return []
        journal_bundles = api_client.get_journal_bundles(uuid=bundle_uuid)
        cache.set(cache_key, journal_bundles, JOURNALS_CACHE_TIMEOUT)

    if isinstance(journal_bundles, dict):
        fix_course_images(journal_bundles)
    else:
        for bundle in journal_bundles:
            fix_course_images(bundle)

    return journal_bundles


def get_journals_root_url():
    '''
    Return the base url used to display Journals
    '''
    if journals_enabled():
        return configuration_helpers.get_configuration_value(
            'JOURNALS_URL_ROOT',
            settings.JOURNALS_URL_ROOT
        ) if configuration_helpers.is_site_configuration_enabled() else settings.JOURNALS_URL_ROOT
    else:
        return None
