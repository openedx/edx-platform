"""Helper functions for working with Credentials."""
import logging
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from edx_rest_api_client.auth import SuppliedJwtAuth

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.lib.edx_api_utils import get_api_data

log = logging.getLogger(__name__)
User = get_user_model()


def get_credentials_records_url(program_uuid=None):
    """
    Returns a URL for a given records page (or general records list if given no UUID).
    May return None if this feature is disabled.

    Arguments:
        program_uuid (str): Optional program uuid to link for a program records URL
    """
    base_url = CredentialsApiConfig.current().public_records_url
    if base_url is None:
        return None

    if program_uuid:
        # Credentials expects Program UUIDs without dashes so we remove them here
        stripped_program_uuid = program_uuid.replace("-", "")
        return urljoin(base_url, f"programs/{stripped_program_uuid}")

    return base_url


def get_credentials_api_client(user):
    """
    Returns an authenticated Credentials API client.

    Arguments:
        user (User): The user to authenticate as when requesting credentials.
    """
    scopes = ['email', 'profile', 'user_id']
    jwt = create_jwt_for_user(user, scopes=scopes)

    client = requests.Session()
    client.auth = SuppliedJwtAuth(jwt)
    return client


def get_credentials_api_base_url(org=None):
    """
    Returns a credentials API base URL.

    Arguments:
        org (str): Optional organization to look up the site config for, rather than the current request
    """
    if org is None:
        url = CredentialsApiConfig.current().internal_api_url  # by current request
    else:
        url = CredentialsApiConfig.get_internal_api_url_for_org(org)  # by org

    return url


def get_credentials(user, program_uuid=None, credential_type=None):
    """
    Given a user, get credentials earned from the credentials service.

    Arguments:
        user (User): The user to authenticate as when requesting credentials.

    Keyword Arguments:
        program_uuid (str): UUID of the program whose credential to retrieve.
        credential_type (str): Which type of credentials to return (course-run or program)

    Returns:
        list of dict, representing credentials returned by the Credentials
        service.
    """
    credential_configuration = CredentialsApiConfig.current()

    querystring = {'username': user.username, 'status': 'awarded', 'only_visible': 'True'}

    if program_uuid:
        querystring['program_uuid'] = program_uuid

    if credential_type:
        querystring['type'] = credential_type

    # Bypass caching for staff users, who may be generating credentials and
    # want to see them displayed immediately.
    use_cache = credential_configuration.is_cache_enabled and not user.is_staff
    cache_key = f'{credential_configuration.CACHE_KEY}.{user.username}' if use_cache else None
    if cache_key and program_uuid:
        cache_key = f'{cache_key}.{program_uuid}'

    api_client = get_credentials_api_client(user)
    base_api_url = get_credentials_api_base_url()

    return get_api_data(
        credential_configuration,
        'credentials',
        api_client=api_client,
        base_api_url=base_api_url,
        querystring=querystring,
        cache_key=cache_key
    )


def get_course_completion_status(lms_user_id, course_run_keys):
    """
    Given the lms_user_id and course run ids, checks for course completion status
    Arguments:
        lms_user_id (User): The user to authenticate as when requesting credentials.
        course_run_keys(List): list of course run ids for which we need to check the completion status
    Returns:
        list of course_run_keys for which user has completed the course
    """
    credential_configuration = CredentialsApiConfig.current()
    if not credential_configuration.enabled:
        log.warning('%s configuration is disabled.', credential_configuration.API_NAME)
        return []

    base_api_url = get_credentials_api_base_url()
    completion_status_url = f'{base_api_url}/api/credentials/learner_cert_status'
    try:
        api_client = get_credentials_api_client(
            User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME)
        )
        api_response = api_client.post(
            completion_status_url,
            data={
                'lms_user_id': lms_user_id,
                'course_runs': course_run_keys,
            }
        )
        # TODO: will be fixed in https://2u-internal.atlassian.net/browse/APER-2425
        # We will deal all 404s as valid response for now and return empty response in that case.
        # which means user has not completed any course.
        if api_response.status_code == 404:
            log.info("Encountered a 404 while reqeusting course completion statuses "
                     "for lms_user_id [%s] for course_run_keys [%s]",
                     lms_user_id,
                     course_run_keys,
                     )
            return []
        api_response.raise_for_status()
        course_completion_response = api_response.json()
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("An unexpected error occurred while reqeusting course completion statuses "
                      "for lms_user_id [%s] for course_run_keys [%s] with exc [%s]:",
                      lms_user_id,
                      course_run_keys,
                      exc
                      )
        return []
    if course_completion_response is not None:
        # Yes, This is course_credentials_data. The key is named status but
        # it contains all the courses data from credentials.
        course_credentials_data = course_completion_response.get('status')
        # Based on the first to-do we may need a change here.
        filtered_records = [course_data for course_data in course_credentials_data if
                            course_data['course_run']['key'] in course_run_keys and
                            course_data['status'] == 'awarded']
        return filtered_records
    return []
