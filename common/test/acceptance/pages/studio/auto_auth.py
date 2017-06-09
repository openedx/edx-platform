"""
Auto-auth page (used to automatically log in during testing).
"""

import re
import urllib
from bok_choy.page_object import PageObject
from common.test.acceptance.pages.studio import BASE_URL


class AutoAuthPage(PageObject):
    """
    The automatic authorization page.
    When allowed via the django settings file, visiting
    this url will create/update a user and log them in.
    """

    def __init__(self, browser, username=None, email=None, password=None,
                 staff=None, course_id=None, roles=None, no_login=None, is_active=None):
        """
        Auto-auth is an end-point for HTTP GET requests.
        By default, it will create accounts with random user credentials,
        but you can also specify credentials using querystring parameters.

        Can be used to update an account, call to this end-point with already
        made account's credentials along with values to update will result into
        an account update.

        `username`, `email`, and `password` are the user's credentials (strings)
        `staff` is a boolean indicating whether the user is global staff.
        `course_id` is the ID of the course to enroll the student in.
        `is_active` activation status of user
        Currently, this has the form "org/number/run"

        Note that "global staff" is NOT the same as course staff.
        """
        super(AutoAuthPage, self).__init__(browser)

        # Create query string parameters if provided
        self._params = {}

        if username is not None:
            self._params['username'] = username

        if email is not None:
            self._params['email'] = email

        if password is not None:
            self._params['password'] = password

        if staff is not None:
            self._params['staff'] = "true" if staff else "false"

        if course_id is not None:
            self._params['course_id'] = course_id

        if roles is not None:
            self._params['roles'] = roles

        if no_login:
            self._params['no_login'] = True

        if is_active is not None:
            self._params['is_active'] = 'true' if is_active else 'false'

    @property
    def url(self):
        """
        Construct the URL.
        """
        url = BASE_URL + "/auto_auth"
        query_str = urllib.urlencode(self._params)

        if query_str:
            url += "?" + query_str

        return url

    def is_browser_on_page(self):
        message = self.q(css='BODY').text[0]
        match = re.search(r'(Logged in|Created) user ([^$]+) with password ([^$]+) and user_id ([^$]+)$', message)
        return True if match else False

    def get_user_id(self):
        message = self.q(css='BODY').text[0].strip()
        match = re.search(r' user_id ([^$]+)$', message)
        return match.groups()[0] if match else None
