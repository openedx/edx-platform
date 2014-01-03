"""
Auto-auth page (used to automatically log in during testing).
"""

import urllib
from bok_choy.page_object import PageObject
from . import BASE_URL


class AutoAuthPage(PageObject):
    """
    The automatic authorization page.
    When allowed via the django settings file, visiting
    this url will create a user and log them in.
    """

    name = "studio.auto_auth"

    def url(self, username=None, email=None, password=None, staff=None, course_id=None):  #pylint: disable=W0221
        """
        Auto-auth is an end-point for HTTP GET requests.
        By default, it will create accounts with random user credentials,
        but you can also specify credentials using querystring parameters.

        `username`, `email`, and `password` are the user's credentials (strings)
        `staff` is a boolean indicating whether the user is global staff.
        `course_id` is the ID of the course to enroll the student in.
        Currently, this has the form "org/number/run"

        Note that "global staff" is NOT the same as course staff.
        """

        # The base URL, used for creating a random user
        url = BASE_URL + "/auto_auth"

        # Create query string parameters if provided
        params = {}

        if username is not None:
            params['username'] = username

        if email is not None:
            params['email'] = email

        if password is not None:
            params['password'] = password

        if staff is not None:
            params['staff'] = "true" if staff else "false"

        if course_id is not None:
            params['course_id'] = course_id

        query_str = urllib.urlencode(params)

        # Append the query string to the base URL
        if query_str:
            url += "?" + query_str

        return url

    def is_browser_on_page(self):
        return True
