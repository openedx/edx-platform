"""
Fixture to create a course and course components (XBlocks).
"""

import json
import datetime
from textwrap import dedent
import requests
from lazy import lazy
from bok_choy.web_app_fixture import WebAppFixture, WebAppFixtureError
from . import STUDIO_BASE_URL


class StudioApiFixture(WebAppFixture):
    """
    Base class for fixtures that use the Studio restful API.
    """

    @lazy
    def session_cookies(self):
        """
        Log in as a staff user, then return the cookies for the session (as a dict)
        Raises a `WebAppFixtureError` if the login fails.
        """

        # Use auto-auth to retrieve session cookies for a logged in user
        response = requests.get(STUDIO_BASE_URL + "/auto_auth?staff=true")

        # Return the cookies from the request
        if response.ok:
            return {key: val for key, val in response.cookies.items()}

        else:
            msg = "Could not log in to use Studio restful API.  Status code: {0}".format(response.status_code)
            raise WebAppFixtureError(msg)

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


class XBlockFixtureDesc(object):
    """
    Description of an XBlock, used to configure a course fixture.
    """

    def __init__(self, category, display_name, data=None, metadata=None, grader_type=None, publish='make_public'):
        """
        Configure the XBlock to be created by the fixture.
        These arguments have the same meaning as in the Studio REST API:
            * `category`
            * `display_name`
            * `data`
            * `metadata`
            * `grader_type`
            * `publish`
        """
        self.category = category
        self.display_name = display_name
        self.data = data
        self.metadata = metadata
        self.grader_type = grader_type
        self.publish = publish
        self.children = []

    def add_children(self, *args):
        """
        Add child XBlocks to this XBlock.
        Each item in `args` is an `XBlockFixtureDescriptor` object.

        Returns the `xblock_desc` instance to allow chaining.
        """
        self.children.extend(args)
        return self

    def serialize(self, parent_loc=None):
        """
        Return a JSON representation of the XBlock, suitable
        for sending as POST data to /xblock

        XBlocks are always set to public visibility.
        """
        payload = {
            'category': self.category,
            'display_name': self.display_name,
            'data': self.data,
            'metadata': self.metadata,
            'grader_type': self.grader_type,
            'publish': self.publish
        }

        if parent_loc is not None:
            payload['parent_locator'] = parent_loc

        return json.dumps(payload)

    def __str__(self):
        """
        Return a string representation of the description.
        Useful for error messages.
        """
        return dedent("""
            <XBlockFixtureDescriptor:
                category={0},
                data={1},
                metadata={2},
                grader_type={3},
                publish={4},
                children={5}
            >
        """).strip().format(
            self.category, self.data, self.metadata,
            self.grader_type, self.publish, self.children
        )


class CourseFixture(StudioApiFixture):
    """
    Fixture for ensuring that a course exists.

    WARNING: This fixture is NOT idempotent.  To avoid conflicts
    between tests, you should use unique course identifiers for each fixture.
    """

    def __init__(self, org, number, run, display_name, start_date=None, end_date=None):
        """
        Configure the course fixture to create a course with

        `org`, `number`, `run`, and `display_name` (all unicode).

        `start_date` and `end_date` are datetime objects indicating the course start and end date.
        The default is for the course to have started in the distant past, which is generally what
        we want for testing so students can enroll.

        These have the same meaning as in the Studio restful API /course end-point.
        """
        self._course_dict = {
            'org': org,
            'number': number,
            'run': run,
            'display_name': display_name
        }

        # Set a default start date to the past, but use Studio's
        # default for the end date (meaning we don't set it here)
        if start_date is None:
            start_date = datetime.datetime(1970, 1, 1)

        self._course_details = {
            'start_date': start_date.isoformat(),
        }

        if end_date is not None:
            self._course_details['end_date'] = end_date.isoformat()

        self._children = []

    def __str__(self):
        """
        String representation of the course fixture, useful for debugging.
        """
        return "<CourseFixture: org='{org}', number='{number}', run='{run}'>".format(**self._course_dict)

    def add_children(self, *args):
        """
        Add children XBlock to the course.
        Each item in `args` is an `XBlockFixtureDescriptor` object.

        Returns the course fixture to allow chaining.
        """
        self._children.extend(args)
        return self

    def install(self):
        """
        Create the course and XBlocks within the course.
        This is NOT an idempotent method; if the course already exists, this will
        raise a `WebAppFixtureError`.  You should use unique course identifiers to avoid
        conflicts between tests.
        """
        self._create_course()
        self._configure_course()
        self._create_xblock_children(self._course_loc, self._children)

    @property
    def _course_loc(self):
        """
        Return the locator string for the course.
        """
        return "{org}.{number}.{run}/branch/draft/block/{run}".format(**self._course_dict)

    def _create_course(self):
        """
        Create the course described in the fixture.
        """
        # If the course already exists, this will respond
        # with a 200 and an error message, which we ignore.
        response = requests.post(
            STUDIO_BASE_URL + '/course',
            data=self._encode_post_dict(self._course_dict),
            headers=self.headers,
            cookies=self.session_cookies
        )

        try:
            err = response.json().get('ErrMsg')

        except ValueError:
            raise WebAppFixtureError(
                "Could not parse response from course request as JSON: '{0}'".format(
                    response.content))

        # This will occur if the course identifier is not unique
        if err is not None:
            raise WebAppFixtureError("Could not create course {0}.  Error message: '{1}'".format(self, err))

        if not response.ok:
            raise WebAppFixtureError(
                "Could not create course {0}.  Status was {1}".format(
                    self._course_dict, response.status_code))

    def _configure_course(self):
        """
        Configure course settings (e.g. start and end date)
        """
        url = STUDIO_BASE_URL + '/settings/details/' + self._course_loc

        # First, get the current values
        response = requests.get(url, headers=self.headers, cookies=self.session_cookies)

        if not response.ok:
            raise WebAppFixtureError(
                "Could not retrieve course details.  Status was {0}".format(
                    response.status_code))

        try:
            details = response.json()
        except ValueError:
            raise WebAppFixtureError(
                "Could not decode course details as JSON: '{0}'".format(old_details)
            )

        # Update the old details with our overrides
        details.update(self._course_details)

        # POST the updated details to Studio
        response = requests.post(
            url, data=self._encode_post_dict(details),
            headers=self.headers,
            cookies=self.session_cookies
        )

        if not response.ok:
            raise WebAppFixtureError(
                "Could not update course details to '{0}'.  Status was {1}.".format(
                    self._course_details, response.status_code))

    def _create_xblock_children(self, parent_loc, xblock_descriptions):
        """
        Recursively create XBlock children.
        """
        for desc in xblock_descriptions:
            loc = self._create_xblock(parent_loc, desc)
            self._create_xblock_children(loc, desc.children)

    def _create_xblock(self, parent_loc, xblock_desc):
        """
        Create an XBlock with `parent_loc` (the location of the parent block)
        and `xblock_desc` (an `XBlockFixtureDesc` instance).
        """
        # Create the new XBlock
        response = requests.post(
            STUDIO_BASE_URL + '/xblock',
            data=xblock_desc.serialize(parent_loc=parent_loc),
            headers=self.headers,
            cookies=self.session_cookies
        )

        if not response.ok:
            msg = "Could not create {0}.  Status was {1}".format(xblock_desc, response.status_code)
            raise WebAppFixtureError(msg)

        try:
            loc = response.json().get('locator')

        except ValueError:
            raise WebAppFixtureError("Could not decode JSON from '{0}'".format(response.content))

        if loc is not None:

            # Configure the XBlock
            response = requests.post(
                STUDIO_BASE_URL + '/xblock/' + loc,
                data=xblock_desc.serialize(),
                headers=self.headers,
                cookies=self.session_cookies
            )

            if response.ok:
                return loc
            else:
                raise WebAppFixtureError("Could not update {0}".format(xblock_desc))

        else:
            raise WebAppFixtureError("Could not retrieve location of {0}".format(xblock_desc))

    def _encode_post_dict(self, post_dict):
        """
        Encode `post_dict` (a dictionary) as UTF-8 encoded JSON.
        """
        return json.dumps({
            k: v.encode('utf-8') if v is not None else v
            for k, v in post_dict.items()
        })
