"""
Tests for Learning-Core-based Content Libraries
"""
from datetime import datetime, timezone

import ddt
from freezegun import freeze_time

from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest
from openedx.core.djangolib.testing.utils import skip_unless_cms


@skip_unless_cms
@ddt.ddt
class ContainersTestCase(ContentLibrariesRestApiTest):
    """
    Tests for containers (Sections, Subsections, Units) in Content Libraries.

    These tests use the REST API, which in turn relies on the Python API.
    Some tests may use the python API directly if necessary to provide
    coverage of any code paths not accessible via the REST API.

    In general, these tests should
    (1) Use public APIs only - don't directly create data using other methods,
        which results in a less realistic test and ties the test suite too
        closely to specific implementation details.
        (Exception: users can be provisioned using a user factory)
    (2) Assert that fields are present in responses, but don't assert that the
        entire response has some specific shape. That way, things like adding
        new fields to an API response, which are backwards compatible, won't
        break any tests, but backwards-incompatible API changes will.
    """
    # Note: if we need events at some point, add OpenEdxEventsTestMixin and set the list here; see other test suites.
    # ENABLED_OPENEDX_EVENTS = []

    def test_unit_crud(self):
        """
        Test Create, Read, Update, and Delete of a Unit
        """
        lib = self._create_library(slug="containers", title="Container Test Library", description="Units and more")

        # Create a unit:
        create_date = datetime(2024, 9, 8, 7, 6, 5, tzinfo=timezone.utc)
        with freeze_time(create_date):
            container_data = self._create_container(lib["id"], "unit", slug="u1", display_name="Test Unit")
        expected_data = {
            "container_key": "lct:CL-TEST:containers:unit:u1",
            "container_type": "unit",
            "display_name": "Test Unit",
            "last_published": None,
            "published_by": "",
            "last_draft_created": "2024-09-08T07:06:05Z",
            "last_draft_created_by": 'Bob',
            'has_unpublished_changes': True,
            'created': '2024-09-08T07:06:05Z',
            'modified': '2024-09-08T07:06:05Z',
            'collections': [],
        }

        self.assertDictContainsEntries(container_data, expected_data)

        # Fetch the unit:
        unit_as_read = self._get_container(container_data["container_key"])
        # make sure it contains the same data when we read it back:
        self.assertDictContainsEntries(unit_as_read, expected_data)

    # TODO: test that a regular user with read-only permissions on the library cannot create units

    def test_unit_gets_auto_slugs(self):
        """
        Test that we can create units by specifying only a title, and they get
        unique slugs assigned automatically.
        """
        lib = self._create_library(slug="containers", title="Container Test Library", description="Units and more")

        # Create two units, specifying their titles but not their slugs/keys:
        container1_data = self._create_container(lib["id"], "unit", display_name="Alpha Bravo", slug=None)
        container2_data = self._create_container(lib["id"], "unit", display_name="Alpha Bravo", slug=None)
        # Notice the container IDs below are slugified from the title: "alpha-bravo-NNNNN"
        assert container1_data["container_key"].startswith("lct:CL-TEST:containers:unit:alpha-bravo-")
        assert container2_data["container_key"].startswith("lct:CL-TEST:containers:unit:alpha-bravo-")
        assert container1_data["container_key"] != container2_data["container_key"]
