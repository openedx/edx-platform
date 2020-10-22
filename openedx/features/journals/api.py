"""
APIs providing support for Journals functionality.
"""
from urlparse import urljoin, urlsplit, urlunsplit
import logging
import hashlib
import six

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from edx_rest_api_client.client import EdxRestApiClient
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace
from slumber.exceptions import HttpClientError, HttpServerError


LOGGER = logging.getLogger("edx.journals")
JOURNALS_CACHE_TIMEOUT = 3600  # Value is in seconds
JOURNALS_API_PATH = '/journal/api/v1/'
JOURNAL_WORKER_USERNAME = 'journals_worker'
User = get_user_model()

# Waffle switches namespace for journals
WAFFLE_NAMESPACE = 'journals'
WAFFLE_SWITCHES = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

# Waffle switch for enabling/disabling journals
JOURNAL_INTEGRATION = 'enable_journal_integration'


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
            LOGGER.error("Unable to create DiscoveryApiClient because catalog integration not set up or enabled")
            return None

        try:
            user = catalog_integration.get_service_user()
        except ObjectDoesNotExist:
            LOGGER.error("Unable to retrieve catalog integration service user")
            return None

        jwt = create_jwt_for_user(user)
        base_url = configuration_helpers.get_value('COURSE_CATALOG_URL_BASE', settings.COURSE_CATALOG_URL_BASE)
        self.client = EdxRestApiClient(
            '{base_url}{journals_path}'.format(base_url=base_url, journals_path=JOURNALS_API_PATH),
            jwt=jwt
        )

    def get_journals(self, orgs):
        """
        get_journals from discovery, filter on orgs is supplied
        """
        try:
            if orgs:
                response = self.client.journals.get(orgs=','.join(orgs), status='active')
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
        """
        get_journal_bundles from discovery on the base of uuid (optional)
        """
        try:
            response = self.client.journal_bundles(uuid).get()
        except (HttpClientError, HttpServerError) as err:
            LOGGER.exception(
                'Failed to get journal bundles from discovery-service [%s]',
                err.content
            )
            return []
        return [response] if uuid else response.get('results')


class JournalsApiClient(object):
    """
    Class for interacting with the Journals Service
    """
    def __init__(self):
        """
        Initialize an authenticated Journals service API client by using the
        provided user.
        """
        try:
            self.user = self.get_journals_worker()
        except ObjectDoesNotExist:
            error = 'Unable to retrieve {} service user'.format(JOURNAL_WORKER_USERNAME)
            LOGGER.error(error)
            raise ValueError(error)

        jwt = create_jwt_for_user(self.user)
        self.client = EdxRestApiClient(
            configuration_helpers.get_value('JOURNALS_API_URL', settings.JOURNALS_API_URL),
            jwt=jwt
        )

    def get_journals_worker(self):
        """ Return journals worker """
        return User.objects.get(username=JOURNAL_WORKER_USERNAME)


def fetch_journal_access(site, user, block_id=None):   # pylint: disable=unused-argument
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
    try:
        # TODO: WL-1560:
        # LMS should cache responses from Journal Access API
        # Need strategy for updating cache when new purchase happens
        endpoint_params = {
            "user": user,
            "get_latest": True,
        }
        if block_id:
            endpoint_params['block_id'] = block_id
        journal_access_records = JournalsApiClient().client.journalaccess.get(**endpoint_params)
        return journal_access_records.get('results', [])
    except ValueError:
        return []


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
    Determines whether the Journals app is installed and enabled for the current Site
    Returns:
        True if global setting via waffle switch
        'journals.enable_journal_integration' is enabled and
        Site specific setting JOURNALS_ENABLED is True.
        False if either of these settings is not enabled
    """
    return 'openedx.features.journals.apps.JournalsConfig' in settings.INSTALLED_APPS and \
        WAFFLE_SWITCHES.is_enabled(JOURNAL_INTEGRATION) and \
        configuration_helpers.get_value('JOURNALS_ENABLED', settings.FEATURES.get('JOURNALS_ENABLED', False))


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

    _CACHE_MISS = object()
    journal_bundles = cache.get(cache_key, _CACHE_MISS)

    if journal_bundles is _CACHE_MISS:
        api_client = DiscoveryApiClient()
        if not api_client:
            return []
        journal_bundles = api_client.get_journal_bundles(uuid=bundle_uuid)
        cache.set(cache_key, journal_bundles, JOURNALS_CACHE_TIMEOUT)

    for bundle in journal_bundles:
        fix_course_images(bundle)

    return journal_bundles


def get_journals_root_url():
    """
    Return the base url for the journals service
    """
    if journals_enabled():
        return configuration_helpers.get_value(
            'JOURNALS_URL_ROOT',
            settings.JOURNALS_URL_ROOT
        )
    else:
        return None


def get_journals_frontend_url():
    """
    Return the frontend url used to display Journals
    """
    if journals_enabled():
        return configuration_helpers.get_value(
            'JOURNALS_FRONTEND_URL',
            settings.JOURNALS_FRONTEND_URL
        )
    else:
        return None


def get_journal_about_page_url(about_page_id=0, auth=True):
    """
    Return url to journal about page.
    If auth=True, the url will redirect through the journals service log in page
    which will prevent the "purchase now" button being shown.
    If auth=False, the url will point to Journal About Page with purchase button shown

    Arguments:
        about_page_id (int): id of Journal About Page as found in Discovery
        auth (boolen): authorization flag, if true will force login to journal service
        and redirect to last visited page in Journal after login. If false, this method
        will return direct url to journal about page.

    Returns:
        url (str): url pointing to Journals Service login, w/ a redirect to last visited journal page
        or url pointing directly to journal about page.
    """
    if not auth:
        return urljoin(get_journals_frontend_url(), '{id}/about'.format(id=about_page_id))

    # by providing just the about_page_id in the url, the user will be redirected
    # to the last page viewed after logging in
    about_page_url = urljoin(get_journals_frontend_url(), '{id}'.format(id=about_page_id))
    login_url = urljoin(get_journals_root_url(), 'require_auth')
    query = 'forward={next_url}'.format(next_url=about_page_url)

    split_url = urlsplit(login_url)
    url = urlunsplit((
        split_url.scheme,
        split_url.netloc,
        split_url.path,
        query,
        split_url.fragment,
    ))
    return url


def get_journals_context(request):
    """
    Return dict of Journal context information for a given request

    Args:
        request: The request to process

    Returns:
        dict containing the following information:
        dict['journals'] - list of Journals available for purchase
        dict['journal_bundles'] - list of JournalBundles available for purchase
    """
    journal_info = {}
    journal_info['journals'] = get_journals(request.site)
    journal_info['journal_bundles'] = get_journal_bundles(request.site)

    return journal_info
