"""Helper functions for working with Credentials."""
<<<<<<< HEAD
=======

>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
import logging
from typing import Dict, List
from urllib.parse import urljoin

import requests
<<<<<<< HEAD
from django.conf import settings
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
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


<<<<<<< HEAD
def get_credentials_api_client(user):
=======
def get_credentials_api_client(user) -> requests.Session:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """
    Returns an authenticated Credentials API client.

    Arguments:
        user (User): The user to authenticate as when requesting credentials.
    """
    scopes = ["email", "profile", "user_id"]
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


def get_credentials(
    user: User,
    program_uuid: str = None,
    credential_type: str = None,
    raise_on_error: bool = False,
) -> List[Dict]:
    """
    Given a user, get credentials earned from the credentials service.

    Arguments:
        user (User): The user to authenticate as when requesting credentials.

    Keyword Arguments:
        program_uuid (str): UUID of the program whose credential to retrieve.
        credential_type (str): Which type of credentials to return (course-run or program)
        raise_on_error (bool): Reraise errors back to the caller, instead if returning empty results.

    Returns:
        list of dict, representing credentials returned by the Credentials
        service.
    """
    credential_configuration = CredentialsApiConfig.current()

    querystring = {
        "username": user.username,
        "status": "awarded",
        "only_visible": "True",
    }

    if program_uuid:
        querystring["program_uuid"] = program_uuid

    if credential_type:
        querystring["type"] = credential_type

    # Bypass caching for staff users, who may be generating credentials and
    # want to see them displayed immediately.
    use_cache = credential_configuration.is_cache_enabled and not user.is_staff
<<<<<<< HEAD
    cache_key = (
        f"{credential_configuration.CACHE_KEY}.{user.username}" if use_cache else None
    )
=======
    cache_key = f"{credential_configuration.CACHE_KEY}.{user.username}" if use_cache else None
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    if cache_key and program_uuid:
        cache_key = f"{cache_key}.{program_uuid}"

    api_client = get_credentials_api_client(user)
    base_api_url = get_credentials_api_base_url()

    return get_api_data(
        credential_configuration,
        "credentials",
        api_client=api_client,
        base_api_url=base_api_url,
        querystring=querystring,
        cache_key=cache_key,
        raise_on_error=raise_on_error,
    )
<<<<<<< HEAD


def get_courses_completion_status(username, course_run_ids):
    """
    Given the username and course run ids, checks for course completion status
    Arguments:
        username (User): Username of the user whose credentials are being requested.
        course_run_ids(List): list of course run ids for which we need to check the completion status
    Returns:
        list of course_run_ids for which user has completed the course
        Boolean: True if an exception occurred while calling the api, False otherwise
    """
    credential_configuration = CredentialsApiConfig.current()
    if not credential_configuration.enabled:
        log.warning("%s configuration is disabled.", credential_configuration.API_NAME)
        return [], False

    completion_status_url = (
        f"{settings.CREDENTIALS_INTERNAL_SERVICE_URL}/api"
        "/credentials/v1/learner_cert_status/"
    )
    try:
        api_client = get_credentials_api_client(
            User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME)
        )
        api_response = api_client.post(
            completion_status_url,
            json={
                "username": username,
                "course_runs": course_run_ids,
            },
        )
        api_response.raise_for_status()
        course_completion_response = api_response.json()
    except Exception as exc:  # pylint: disable=broad-except
        log.exception(
            "An unexpected error occurred while reqeusting course completion statuses "
            "for user [%s] for course_run_ids [%s] with exc [%s]:",
            username,
            course_run_ids,
            exc,
        )
        return [], True
    log.info(
        "Course completion status response for user [%s] for course_run_ids [%s] is [%s]",
        username,
        course_run_ids,
        course_completion_response,
    )
    # Yes, This is course_credentials_data. The key is named status but
    # it contains all the courses data from credentials.
    course_credentials_data = course_completion_response.get("status", [])
    if course_credentials_data is not None:
        filtered_records = [
            course_data["course_run"]["key"]
            for course_data in course_credentials_data
            if course_data["course_run"]["key"] in course_run_ids
            and course_data["status"] == settings.CREDENTIALS_COURSE_COMPLETION_STATE
        ]
        return filtered_records, False
    return [], False
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
