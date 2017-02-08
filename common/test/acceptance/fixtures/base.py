"""
Common code shared by course and library fixtures.
"""
import re
import requests
import json
from lazy import lazy

from common.test.acceptance.fixtures import STUDIO_BASE_URL


class StudioApiLoginError(Exception):
    """
    Error occurred while logging in to the Studio API.
    """
    pass


class StudioApiFixture(object):
    """
    Base class for fixtures that use the Studio restful API.
    """
    def __init__(self):
        # Info about the auto-auth user used to create the course/library.
        self.user = {}

    @lazy
    def session(self):
        """
        Log in as a staff user, then return a `requests` `session` object for the logged in user.
        Raises a `StudioApiLoginError` if the login fails.
        """
        # Use auto-auth to retrieve the session for a logged in user
        session = requests.Session()
        response = session.get(STUDIO_BASE_URL + "/auto_auth?staff=true")

        # Return the session from the request
        if response.ok:
            # auto_auth returns information about the newly created user
            # capture this so it can be used by by the testcases.
            user_pattern = re.compile(r'Logged in user {0} \({1}\) with password {2} and user_id {3}'.format(
                r'(?P<username>\S+)', r'(?P<email>[^\)]+)', r'(?P<password>\S+)', r'(?P<user_id>\d+)'))
            user_matches = re.match(user_pattern, response.text)
            if user_matches:
                self.user = user_matches.groupdict()

            return session

        else:
            msg = "Could not log in to use Studio restful API.  Status code: {0}".format(response.status_code)
            raise StudioApiLoginError(msg)

    @lazy
    def session_cookies(self):
        """
        Log in as a staff user, then return the cookies for the session (as a dict)
        Raises a `StudioApiLoginError` if the login fails.
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


class FixtureError(Exception):
    """
    Error occurred while installing a course or library fixture.
    """
    pass


class XBlockContainerFixture(StudioApiFixture):
    """
    Base class for course and library fixtures.
    """

    def __init__(self):
        self.children = []
        super(XBlockContainerFixture, self).__init__()

    def add_children(self, *args):
        """
        Add children XBlock to the container.
        Each item in `args` is an `XBlockFixtureDesc` object.

        Returns the fixture to allow chaining.
        """
        self.children.extend(args)
        return self

    def _create_xblock_children(self, parent_loc, xblock_descriptions):
        """
        Recursively create XBlock children.
        """
        for desc in xblock_descriptions:
            loc = self.create_xblock(parent_loc, desc)
            self._create_xblock_children(loc, desc.children)

    def create_xblock(self, parent_loc, xblock_desc):
        """
        Create an XBlock with `parent_loc` (the location of the parent block)
        and `xblock_desc` (an `XBlockFixtureDesc` instance).
        """
        create_payload = {
            'category': xblock_desc.category,
            'display_name': xblock_desc.display_name,
        }

        if parent_loc is not None:
            create_payload['parent_locator'] = parent_loc

        # Create the new XBlock
        response = self.session.post(
            STUDIO_BASE_URL + '/xblock/',
            data=json.dumps(create_payload),
            headers=self.headers,
        )

        if not response.ok:
            msg = "Could not create {0}.  Status was {1}".format(xblock_desc, response.status_code)
            raise FixtureError(msg)

        try:
            loc = response.json().get('locator')
            xblock_desc.locator = loc
        except ValueError:
            raise FixtureError("Could not decode JSON from '{0}'".format(response.content))

        # Configure the XBlock
        response = self.session.post(
            STUDIO_BASE_URL + '/xblock/' + loc,
            data=xblock_desc.serialize(),
            headers=self.headers,
        )

        if response.ok:
            return loc
        else:
            raise FixtureError("Could not update {0}.  Status code: {1}".format(xblock_desc, response.status_code))

    def _update_xblock(self, locator, data):
        """
        Update the xblock at `locator`.
        """
        # Create the new XBlock
        response = self.session.put(
            "{}/xblock/{}".format(STUDIO_BASE_URL, locator),
            data=json.dumps(data),
            headers=self.headers,
        )

        if not response.ok:
            msg = "Could not update {} with data {}.  Status was {}".format(locator, data, response.status_code)
            raise FixtureError(msg)

    def _encode_post_dict(self, post_dict):
        """
        Encode `post_dict` (a dictionary) as UTF-8 encoded JSON.
        """
        return json.dumps({
            k: v.encode('utf-8') if isinstance(v, basestring) else v
            for k, v in post_dict.items()
        })

    def get_nested_xblocks(self, category=None):
        """
        Return a list of nested XBlocks for the container that can be filtered by
        category.
        """
        xblocks = self._get_nested_xblocks(self)
        if category:
            xblocks = [x for x in xblocks if x.category == category]
        return xblocks

    def _get_nested_xblocks(self, xblock_descriptor):
        """
        Return a list of nested XBlocks for the container.
        """
        xblocks = list(xblock_descriptor.children)
        for child in xblock_descriptor.children:
            xblocks.extend(self._get_nested_xblocks(child))
        return xblocks

    def _publish_xblock(self, locator):
        """
        Publish the xblock at `locator`.
        """
        self._update_xblock(locator, {'publish': 'make_public'})
