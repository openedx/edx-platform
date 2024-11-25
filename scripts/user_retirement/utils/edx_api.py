"""
edX API classes which call edX service REST API endpoints using the edx-rest-api-client module.
"""
<<<<<<< HEAD
=======

>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
import logging
from urllib.parse import urljoin

import backoff
import requests
from edx_rest_api_client.auth import SuppliedJwtAuth
from edx_rest_api_client.client import REQUEST_CONNECT_TIMEOUT, REQUEST_READ_TIMEOUT
from requests.exceptions import ConnectionError, HTTPError, Timeout

from scripts.user_retirement.utils.exception import HttpDoesNotExistException

LOG = logging.getLogger(__name__)

OAUTH_ACCESS_TOKEN_URL = "/oauth2/access_token"


class EdxGatewayTimeoutError(Exception):
    """
    Exception used to indicate a 504 server error was returned.
    Differentiates from other 5xx errors.
    """


class BaseApiClient:
    """
    API client base class used to submit API requests to a particular web service.
    """
<<<<<<< HEAD
=======

>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    append_slash = True
    _access_token = None

    def __init__(self, lms_base_url, api_base_url, client_id, client_secret):
        """
        Retrieves OAuth access token from the LMS and creates REST API client instance.
        """
        self.api_base_url = api_base_url
        self._access_token = self.get_access_token(lms_base_url, client_id, client_secret)

    def get_api_url(self, path):
        """
        Construct the full API URL using the api_base_url and path.

        Args:
            path (str): API endpoint path.
        """
<<<<<<< HEAD
        path = path.strip('/')
        if self.append_slash:
            path += '/'

        return urljoin(f'{self.api_base_url}/', path)

    def _request(self, method, url, log_404_as_error=True, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {'Content-type': 'application/json'}
=======
        path = path.strip("/")
        if self.append_slash:
            path += "/"

        return urljoin(f"{self.api_base_url}/", path)

    def _request(self, method, url, log_404_as_error=True, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = {"Content-type": "application/json"}
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

        try:
            response = requests.request(method, url, auth=SuppliedJwtAuth(self._access_token), **kwargs)
            response.raise_for_status()

            if response.status_code != 204:
                return response.json()
        except HTTPError as exc:
            status_code = exc.response.status_code

            if status_code == 404 and not log_404_as_error:
                # Immediately raise the error so that a 404 isn't logged as an API error in this case.
                raise HttpDoesNotExistException(str(exc))

<<<<<<< HEAD
            LOG.error(f'API Error: {str(exc)} with status code: {status_code}')
=======
            LOG.error(f"API Error: {str(exc)} with status code: {status_code}")
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

            if status_code == 504:
                # Differentiate gateway errors so different backoff can be used.
                raise EdxGatewayTimeoutError(str(exc))

            if status_code == 404:
                raise HttpDoesNotExistException(str(exc))
            raise

        except Timeout:
            LOG.error("The request is timed out.")
            raise

        return response

    @staticmethod
    def get_access_token(oauth_base_url, client_id, client_secret):
        """
        Returns an access token for this site's service user.

        Returns:
            str: JWT access token
        """
<<<<<<< HEAD
        oauth_access_token_url = urljoin(f'{oauth_base_url}/', OAUTH_ACCESS_TOKEN_URL)
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'token_type': 'jwt',
=======
        oauth_access_token_url = urljoin(f"{oauth_base_url}/", OAUTH_ACCESS_TOKEN_URL)
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "token_type": "jwt",
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        }
        try:
            response = requests.post(
                oauth_access_token_url,
                data=data,
                headers={
<<<<<<< HEAD
                    'User-Agent': 'scripts.user_retirement',
                },
                timeout=(REQUEST_CONNECT_TIMEOUT, REQUEST_READ_TIMEOUT)
            )
            response.raise_for_status()
            return response.json()['access_token']
        except KeyError as exc:
            LOG.error(f'Failed to get token. {str(exc)} does not exist.')
=======
                    "User-Agent": "scripts.user_retirement",
                },
                timeout=(REQUEST_CONNECT_TIMEOUT, REQUEST_READ_TIMEOUT),
            )
            response.raise_for_status()
            return response.json()["access_token"]
        except KeyError as exc:
            LOG.error(f"Failed to get token. {str(exc)} does not exist.")
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            raise

        except HTTPError as exc:
            LOG.error(
<<<<<<< HEAD
                f'API Error: {str(exc)} with status code: {exc.response.status_code} fetching access token: {client_id}'
=======
                f"API Error: {str(exc)} with status code: {exc.response.status_code} fetching access token: {client_id}"
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            )
            raise


def _backoff_handler(details):
    """
    Simple logging handler for when timeout backoff occurs.
    """
<<<<<<< HEAD
    LOG.info('Trying again in {wait:0.1f} seconds after {tries} tries calling {target}'.format(**details))
=======
    LOG.info("Trying again in {wait:0.1f} seconds after {tries} tries calling {target}".format(**details))
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374


def _wait_one_minute():
    """
    Backoff generator that waits for 60 seconds.
    """
    return backoff.constant(interval=60)


def _giveup_on_unexpected_exception(exc):
    """
    Giveup method that gives up backoff upon any unexpected exception.
    """
    keep_retrying = (
        # Treat a ConnectionError as retryable.
        isinstance(exc, ConnectionError)
        # All 5xx status codes are retryable except for 504 Gateway Timeout.
<<<<<<< HEAD
        or (
            500 <= exc.response.status_code < 600
            and exc.response.status_code != 504  # Gateway Timeout
        )
=======
        or (500 <= exc.response.status_code < 600 and exc.response.status_code != 504)  # Gateway Timeout
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        # Status code 104 is unreserved, but we must have added this because we observed retryable 104 responses.
        or exc.response.status_code == 104
    )
    return not keep_retrying


def _retry_lms_api():
    """
    Decorator which enables retries with sane backoff defaults for LMS APIs.
    """

    def inner(func):  # pylint: disable=missing-docstring
        func_with_backoff = backoff.on_exception(
            backoff.expo,
            (HTTPError, ConnectionError),
            max_time=600,  # 10 minutes
            giveup=_giveup_on_unexpected_exception,
            # Wrap the actual _backoff_handler so that we can patch the real one in unit tests.  Otherwise, the func
            # will get decorated on import, embedding this handler as a python object reference, precluding our ability
            # to patch it in tests.
<<<<<<< HEAD
            on_backoff=lambda details: _backoff_handler(details)  # pylint: disable=unnecessary-lambda
=======
            on_backoff=lambda details: _backoff_handler(details),  # pylint: disable=unnecessary-lambda
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        )
        func_with_timeout_backoff = backoff.on_exception(
            _wait_one_minute,
            EdxGatewayTimeoutError,
            max_tries=2,
            # Wrap the actual _backoff_handler so that we can patch the real one in unit tests.  Otherwise, the func
            # will get decorated on import, embedding this handler as a python object reference, precluding our ability
            # to patch it in tests.
<<<<<<< HEAD
            on_backoff=lambda details: _backoff_handler(details)  # pylint: disable=unnecessary-lambda
=======
            on_backoff=lambda details: _backoff_handler(details),  # pylint: disable=unnecessary-lambda
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        )
        return func_with_backoff(func_with_timeout_backoff(func))

    return inner


class LmsApi(BaseApiClient):
    """
    LMS API client with convenience methods for making API calls.
    """

    @_retry_lms_api()
    def learners_to_retire(self, states_to_request, cool_off_days=7, limit=None):
        """
        Retrieves a list of learners awaiting retirement actions.
        """
<<<<<<< HEAD
        params = {
            'cool_off_days': cool_off_days,
            'states': states_to_request
        }
        if limit:
            params['limit'] = limit
        api_url = self.get_api_url('api/user/v1/accounts/retirement_queue')
        return self._request('GET', api_url, params=params)
=======
        params = {"cool_off_days": cool_off_days, "states": states_to_request}
        if limit:
            params["limit"] = limit
        api_url = self.get_api_url("api/user/v1/accounts/retirement_queue")
        return self._request("GET", api_url, params=params)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def get_learners_by_date_and_status(self, state_to_request, start_date, end_date):
        """
        Retrieves a list of learners in the given retirement state that were
        created in the retirement queue between the dates given. Date range
        is inclusive, so to get one day you would set both dates to that day.

        :param state_to_request: String LMS UserRetirementState state name (ex. COMPLETE)
        :param start_date: Date or Datetime object
        :param end_date: Date or Datetime
        """
        params = {
<<<<<<< HEAD
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'state': state_to_request
        }
        api_url = self.get_api_url('api/user/v1/accounts/retirements_by_status_and_date')
        return self._request('GET', api_url, params=params)
=======
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "state": state_to_request,
        }
        api_url = self.get_api_url("api/user/v1/accounts/retirements_by_status_and_date")
        return self._request("GET", api_url, params=params)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def get_learner_retirement_state(self, username):
        """
        Retrieves the given learner's retirement state.
        """
<<<<<<< HEAD
        api_url = self.get_api_url(f'api/user/v1/accounts/{username}/retirement_status')
        return self._request('GET', api_url)
=======
        api_url = self.get_api_url(f"api/user/v1/accounts/{username}/retirement_status")
        return self._request("GET", api_url)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def update_learner_retirement_state(self, username, new_state_name, message, force=False):
        """
        Updates the given learner's retirement state to the retirement state name new_string
        with the additional string information in message (for logging purposes).
        """
<<<<<<< HEAD
        data = {
            'username': username,
            'new_state': new_state_name,
            'response': message
        }

        if force:
            data['force'] = True

        api_url = self.get_api_url('api/user/v1/accounts/update_retirement_status')
        return self._request('PATCH', api_url, json=data)
=======
        data = {"username": username, "new_state": new_state_name, "response": message}

        if force:
            data["force"] = True

        api_url = self.get_api_url("api/user/v1/accounts/update_retirement_status")
        return self._request("PATCH", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_deactivate_logout(self, learner):
        """
        Performs the user deactivation and forced logout step of learner retirement
        """
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        api_url = self.get_api_url('api/user/v1/accounts/deactivate_logout')
        return self._request('POST', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        api_url = self.get_api_url("api/user/v1/accounts/deactivate_logout")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_retire_forum(self, learner):
        """
        Performs the forum retirement step of learner retirement
        """
        # api/discussion/
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        try:
            api_url = self.get_api_url('api/discussion/v1/accounts/retire_forum')
            return self._request('POST', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        try:
            api_url = self.get_api_url("api/discussion/v1/accounts/retire_forum")
            return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        except HttpDoesNotExistException:
            LOG.info("No information about learner retirement")
            return True

    @_retry_lms_api()
    def retirement_retire_mailings(self, learner):
        """
        Performs the email list retirement step of learner retirement
        """
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        api_url = self.get_api_url('api/user/v1/accounts/retire_mailings')
        return self._request('POST', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        api_url = self.get_api_url("api/user/v1/accounts/retire_mailings")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_unenroll(self, learner):
        """
        Unenrolls the user from all courses
        """
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        api_url = self.get_api_url('api/enrollment/v1/unenroll')
        return self._request('POST', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        api_url = self.get_api_url("api/enrollment/v1/unenroll")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    # This endpoint additionally returns 500 when the EdxNotes backend service is unavailable.
    @_retry_lms_api()
    def retirement_retire_notes(self, learner):
        """
        Deletes all the user's notes (aka. annotations)
        """
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        api_url = self.get_api_url('api/edxnotes/v1/retire_user')
        return self._request('POST', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        api_url = self.get_api_url("api/edxnotes/v1/retire_user")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_lms_retire_misc(self, learner):
        """
        Deletes, blanks, or one-way hashes personal information in LMS as
        defined in EDUCATOR-2802 and sub-tasks.
        """
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        api_url = self.get_api_url('api/user/v1/accounts/retire_misc')
        return self._request('POST', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        api_url = self.get_api_url("api/user/v1/accounts/retire_misc")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_lms_retire(self, learner):
        """
        Deletes, blanks, or one-way hashes all remaining personal information in LMS
        """
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        api_url = self.get_api_url('api/user/v1/accounts/retire')
        return self._request('POST', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        api_url = self.get_api_url("api/user/v1/accounts/retire")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_partner_queue(self, learner):
        """
        Calls LMS to add the given user to the retirement reporting queue
        """
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        api_url = self.get_api_url('api/user/v1/accounts/retirement_partner_report')
        return self._request('PUT', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        api_url = self.get_api_url("api/user/v1/accounts/retirement_partner_report")
        return self._request("PUT", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_partner_report(self):
        """
        Retrieves the list of users to create partner reports for and set their status to
        processing
        """
<<<<<<< HEAD
        api_url = self.get_api_url('api/user/v1/accounts/retirement_partner_report')
        return self._request('POST', api_url)
=======
        api_url = self.get_api_url("api/user/v1/accounts/retirement_partner_report")
        return self._request("POST", api_url)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_partner_cleanup(self, usernames):
        """
        Removes the given users from the partner reporting queue
        """
<<<<<<< HEAD
        api_url = self.get_api_url('api/user/v1/accounts/retirement_partner_report_cleanup')
        return self._request('POST', api_url, json=usernames)
=======
        api_url = self.get_api_url("api/user/v1/accounts/retirement_partner_report_cleanup")
        return self._request("POST", api_url, json=usernames)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_retire_proctoring_data(self, learner):
        """
        Deletes or hashes learner data from edx-proctoring
        """
        api_url = self.get_api_url(f"api/edx_proctoring/v1/retire_user/{learner['user']['id']}")
<<<<<<< HEAD
        return self._request('POST', api_url)
=======
        return self._request("POST", api_url)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def retirement_retire_proctoring_backend_data(self, learner):
        """
        Removes the given learner from 3rd party proctoring backends
        """
        api_url = self.get_api_url(f"api/edx_proctoring/v1/retire_backend_user/{learner['user']['id']}")
<<<<<<< HEAD
        return self._request('POST', api_url)
=======
        return self._request("POST", api_url)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def bulk_cleanup_retirements(self, usernames):
        """
        Deletes the retirements for all given usernames
        """
<<<<<<< HEAD
        data = {'usernames': usernames}
        api_url = self.get_api_url('api/user/v1/accounts/retirement_cleanup')
        return self._request('POST', api_url, json=data)
=======
        data = {"usernames": usernames}
        api_url = self.get_api_url("api/user/v1/accounts/retirement_cleanup")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    def replace_lms_usernames(self, username_mappings):
        """
        Calls LMS API to replace usernames.

        Param:
            username_mappings: list of dicts where key is current username and value is new desired username
            [{current_un_1: desired_un_1}, {current_un_2: desired_un_2}]
        """
        data = {"username_mappings": username_mappings}
<<<<<<< HEAD
        api_url = self.get_api_url('api/user/v1/accounts/replace_usernames')
        return self._request('POST', api_url, json=data)
=======
        api_url = self.get_api_url("api/user/v1/accounts/replace_usernames")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    def replace_forums_usernames(self, username_mappings):
        """
        Calls the discussion forums API inside of LMS to replace usernames.

        Param:
            username_mappings: list of dicts where key is current username and value is new unique username
            [{current_un_1: new_un_1}, {current_un_2: new_un_2}]
        """
        data = {"username_mappings": username_mappings}
<<<<<<< HEAD
        api_url = self.get_api_url('api/discussion/v1/accounts/replace_usernames')
        return self._request('POST', api_url, json=data)
=======
        api_url = self.get_api_url("api/discussion/v1/accounts/replace_usernames")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374


class EcommerceApi(BaseApiClient):
    """
    Ecommerce API client with convenience methods for making API calls.
    """

    @_retry_lms_api()
    def retire_learner(self, learner):
        """
        Performs the learner retirement step for Ecommerce
        """
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        api_url = self.get_api_url('api/v2/user/retire')
        return self._request('POST', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        api_url = self.get_api_url("api/v2/user/retire")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    @_retry_lms_api()
    def get_tracking_key(self, learner):
        """
        Fetches the ecommerce tracking id used for Segment tracking when
        ecommerce doesn't have access to the LMS user id.
        """
        api_url = self.get_api_url(f"api/v2/retirement/tracking_id/{learner['original_username']}")
<<<<<<< HEAD
        return self._request('GET', api_url)['ecommerce_tracking_id']
=======
        return self._request("GET", api_url)["ecommerce_tracking_id"]
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    def replace_usernames(self, username_mappings):
        """
        Calls the ecommerce API to replace usernames.

        Param:
            username_mappings: list of dicts where key is current username and value is new unique username
            [{current_un_1: new_un_1}, {current_un_2: new_un_2}]
        """
        data = {"username_mappings": username_mappings}
<<<<<<< HEAD
        api_url = self.get_api_url('api/v2/user_management/replace_usernames')
        return self._request('POST', api_url, json=data)
=======
        api_url = self.get_api_url("api/v2/user_management/replace_usernames")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374


class CredentialsApi(BaseApiClient):
    """
    Credentials API client with convenience methods for making API calls.
    """

    @_retry_lms_api()
    def retire_learner(self, learner):
        """
        Performs the learner retirement step for Credentials
        """
<<<<<<< HEAD
        data = {'username': learner['original_username']}
        api_url = self.get_api_url('user/retire')
        return self._request('POST', api_url, json=data)
=======
        data = {"username": learner["original_username"]}
        api_url = self.get_api_url("user/retire")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    def replace_usernames(self, username_mappings):
        """
        Calls the credentials API to replace usernames.

        Param:
            username_mappings: list of dicts where key is current username and value is new unique username
            [{current_un_1: new_un_1}, {current_un_2: new_un_2}]
        """
        data = {"username_mappings": username_mappings}
<<<<<<< HEAD
        api_url = self.get_api_url('api/v2/replace_usernames')
        return self._request('POST', api_url, json=data)
=======
        api_url = self.get_api_url("api/v2/replace_usernames")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374


class DiscoveryApi(BaseApiClient):
    """
    Discovery API client with convenience methods for making API calls.
    """

    def replace_usernames(self, username_mappings):
        """
        Calls the discovery API to replace usernames.

        Param:
            username_mappings: list of dicts where key is current username and value is new unique username
            [{current_un_1: new_un_1}, {current_un_2: new_un_2}]
        """
        data = {"username_mappings": username_mappings}
<<<<<<< HEAD
        api_url = self.get_api_url('api/v1/replace_usernames')
        return self._request('POST', api_url, json=data)


class DemographicsApi(BaseApiClient):
    """
    Demographics API client.
    """

    @_retry_lms_api()
    def retire_learner(self, learner):
        """
        Performs the learner retirement step for Demographics. Passes the learner's LMS User Id instead of username.
        """
        data = {'lms_user_id': learner['user']['id']}
        # If the user we are retiring has no data in the Demographics DB the request will return a 404. We
        # catch the HTTPError and return True in order to prevent this error getting raised and
        # incorrectly causing the learner to enter an ERROR state during retirement.
        try:
            api_url = self.get_api_url('demographics/api/v1/retire_demographics')
            return self._request('POST', api_url, log_404_as_error=False, json=data)
        except HttpDoesNotExistException:
            LOG.info("No demographics data found for user")
            return True
=======
        api_url = self.get_api_url("api/v1/replace_usernames")
        return self._request("POST", api_url, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374


class LicenseManagerApi(BaseApiClient):
    """
    License Manager API client.
    """

    @_retry_lms_api()
    def retire_learner(self, learner):
        """
        Performs the learner retirement step for License manager. Passes the learner's LMS User Id in addition to
        username.
        """
        data = {
<<<<<<< HEAD
            'lms_user_id': learner['user']['id'],
            'original_username': learner['original_username'],
=======
            "lms_user_id": learner["user"]["id"],
            "original_username": learner["original_username"],
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        }
        # If the user we are retiring has no data in the License Manager DB the request will return a 404. We
        # catch the HTTPError and return True in order to prevent this error getting raised and
        # incorrectly causing the learner to enter an ERROR state during retirement.
        try:
<<<<<<< HEAD
            api_url = self.get_api_url('api/v1/retire_user')
            return self._request('POST', api_url, log_404_as_error=False, json=data)
=======
            api_url = self.get_api_url("api/v1/retire_user")
            return self._request("POST", api_url, log_404_as_error=False, json=data)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        except HttpDoesNotExistException:
            LOG.info("No license manager data found for user")
            return True
