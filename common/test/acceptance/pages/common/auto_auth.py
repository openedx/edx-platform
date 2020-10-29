"""
Auto-auth page (used to automatically log in during testing).
"""


import json
import os

from six.moves import urllib
from bok_choy.page_object import PageObject, unguarded

# The URL used for user auth in testing
HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', 'localhost')
CMS_PORT = os.environ.get('BOK_CHOY_CMS_PORT', 8031)
AUTH_BASE_URL = os.environ.get('test_url', 'http://{}:{}'.format(HOSTNAME, CMS_PORT))
FULL_NAME = 'Test'


class AutoAuthPage(PageObject):
    """
    The automatic authorization page.

    When enabled via the Django settings file, visiting this url will create a user and log them in.
    """

    # Internal cache for parsed user info.
    _user_info = None

    def __init__(self, browser, username=None, email=None, password=None, full_name=FULL_NAME, staff=False,
                 superuser=None, course_id=None, enrollment_mode=None, roles=None, no_login=False, is_active=True,
                 course_access_roles=None, should_manually_verify=False):
        """
        Auto-auth is an end-point for HTTP GET requests.
        By default, it will create accounts with random user credentials,
        but you can also specify credentials using querystring parameters.

        `username`, `email`, and `password` are the user's credentials (strings)
        'full_name' is the profile full name value
        `staff` is a boolean indicating whether the user is global staff.
        `superuser` is a boolean indicating whether the user is a super user.
        `course_id` is the ID of the course to enroll the student in.
        Currently, this has the form "org/number/run"
        `should_manually_verify` is a boolean indicating whether the
        created user should have their identification verified

        Note that "global staff" is NOT the same as course staff.
        """
        super(AutoAuthPage, self).__init__(browser)

        # This will eventually hold the details about the user account
        self._user_info = None

        course_access_roles = course_access_roles or []
        course_access_roles = ','.join(course_access_roles)

        self._params = {
            'full_name': full_name,
            'staff': staff,
            'superuser': superuser,
            'is_active': is_active,
            'course_access_roles': course_access_roles,
        }

        if username:
            self._params['username'] = username

        if email:
            self._params['email'] = email

        if password:
            self._params['password'] = password

        if superuser is not None:
            self._params['superuser'] = "true" if superuser else "false"

        if course_id:
            self._params['course_id'] = course_id

            if enrollment_mode:
                self._params['enrollment_mode'] = enrollment_mode

        if roles:
            self._params['roles'] = roles

        if no_login:
            self._params['no_login'] = True

        if should_manually_verify:
            self._params['should_manually_verify'] = True

    @property
    def url(self):
        """
        Construct the URL.
        """
        url = AUTH_BASE_URL + "/auto_auth"
        query_str = urllib.parse.urlencode(self._params)

        if query_str:
            url += "?" + query_str

        return url

    def is_browser_on_page(self):
        return bool(self.user_info)

    @property
    @unguarded
    def user_info(self):
        """A dictionary containing details about the user account."""
        if not self._user_info:
            body = self.q(css='BODY').text[0]
            self._user_info = json.loads(body)

        return self._user_info

    def get_user_id(self):
        """
        Finds and returns the user_id
        """
        return self.user_info['user_id']
