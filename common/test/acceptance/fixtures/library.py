"""
Fixture to create a Content Library
"""

from opaque_keys.edx.keys import CourseKey

from common.test.acceptance.fixtures import STUDIO_BASE_URL
from common.test.acceptance.fixtures.base import XBlockContainerFixture, FixtureError


class LibraryFixture(XBlockContainerFixture):
    """
    Fixture for ensuring that a library exists.

    WARNING: This fixture is NOT idempotent.  To avoid conflicts
    between tests, you should use unique library identifiers for each fixture.
    """

    def __init__(self, org, number, display_name):
        """
        Configure the library fixture to create a library with
        """
        super(LibraryFixture, self).__init__()
        self.library_info = {
            'org': org,
            'number': number,
            'display_name': display_name
        }

        self.display_name = display_name
        self._library_key = None
        super(LibraryFixture, self).__init__()

    def __str__(self):
        """
        String representation of the library fixture, useful for debugging.
        """
        return "<LibraryFixture: org='{org}', number='{number}'>".format(**self.library_info)

    def install(self):
        """
        Create the library and XBlocks within the library.
        This is NOT an idempotent method; if the library already exists, this will
        raise a `FixtureError`.  You should use unique library identifiers to avoid
        conflicts between tests.
        """
        self._create_library()
        self._create_xblock_children(self.library_location, self.children)

        return self

    @property
    def library_key(self):
        """
        Get the LibraryLocator for this library, as a string.
        """
        return self._library_key

    @property
    def library_location(self):
        """
        Return the locator string for the LibraryRoot XBlock that is the root of the library hierarchy.
        """
        lib_key = CourseKey.from_string(self._library_key)
        return unicode(lib_key.make_usage_key('library', 'library'))

    def _create_library(self):
        """
        Create the library described in the fixture.
        Will fail if the library already exists.
        """
        response = self.session.post(
            STUDIO_BASE_URL + '/library/',
            data=self._encode_post_dict(self.library_info),
            headers=self.headers
        )

        if response.ok:
            self._library_key = response.json()['library_key']
        else:
            try:
                err_msg = response.json().get('ErrMsg')
            except ValueError:
                err_msg = "Unknown Error"
            raise FixtureError("Could not create library {}. Status was {}, error was: {}".format(
                self.library_info, response.status_code, err_msg
            ))

    def create_xblock(self, parent_loc, xblock_desc):
        # Disable publishing for library XBlocks:
        xblock_desc.publish = "not-applicable"

        return super(LibraryFixture, self).create_xblock(parent_loc, xblock_desc)
