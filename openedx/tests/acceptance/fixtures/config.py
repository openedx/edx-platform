"""
Fixture to manipulate configuration models.
"""
import requests
import re
import json

from lazy import lazy
from openedx.tests.acceptance.fixtures import LMS_BASE_URL


class ConfigModelFixtureError(Exception):
    """
    Error occurred while configuring the stub XQueue.
    """
    pass


class ConfigModelFixture(object):
    """
    Configure a ConfigurationModel by using it's JSON api.
    """

    def __init__(self, api_base, configuration):
        """
        Configure a ConfigurationModel exposed at `api_base` to have the configuration `configuration`.
        """
        self._api_base = api_base
        self._configuration = configuration

    def install(self):
        """
        Configure the stub via HTTP.
        """
        url = LMS_BASE_URL + self._api_base

        response = self.session.post(
            url,
            data=json.dumps(self._configuration),
            headers=self.headers,
        )

        if not response.ok:
            raise ConfigModelFixtureError(
                "Could not configure url '{}'.  response: {} - {}".format(
                    self._api_base,
                    response,
                    response.content,
                )
            )

    @lazy
    def session_cookies(self):
        """
        Log in as a staff user, then return the cookies for the session (as a dict)
        Raises a `ConfigModelFixtureError` if the login fails.
        """
        return {key: val for key, val in self.session.cookies.items()}

    @lazy
    def headers(self):
        """
        Default HTTP headers dict.
        """
        return {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'X-CSRFToken': self.session_cookies.get('csrftoken', '')
        }

    @lazy
    def session(self):
        """
        Log in as a staff user, then return a `requests` `session` object for the logged in user.
        Raises a `StudioApiLoginError` if the login fails.
        """
        # Use auto-auth to retrieve the session for a logged in user
        session = requests.Session()
        response = session.get(LMS_BASE_URL + "/auto_auth?superuser=true")

        # Return the session from the request
        if response.ok:
            # auto_auth returns information about the newly created user
            # capture this so it can be used by by the testcases.
            user_pattern = re.compile(r'Logged in user {0} \({1}\) with password {2} and user_id {3}'.format(
                r'(?P<username>\S+)', r'(?P<email>[^\)]+)', r'(?P<password>\S+)', r'(?P<user_id>\d+)'))
            user_matches = re.match(user_pattern, response.text)
            if user_matches:
                self.user = user_matches.groupdict()  # pylint: disable=attribute-defined-outside-init

            return session

        else:
            msg = "Could not log in to use ConfigModel restful API.  Status code: {0}".format(response.status_code)
            raise ConfigModelFixtureError(msg)
