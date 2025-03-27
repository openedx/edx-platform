"""
Tests for Learning-Core-based Content Libraries
"""
from datetime import datetime, timezone
from unittest import mock

import ddt
from freezegun import freeze_time

from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_events.content_authoring.data import LibraryContainerData
from openedx_events.content_authoring.signals import (
    LIBRARY_CONTAINER_CREATED,
    LIBRARY_CONTAINER_DELETED,
    LIBRARY_CONTAINER_UPDATED,
)
from openedx_events.tests.utils import OpenEdxEventsTestMixin

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest
from openedx.core.djangolib.testing.utils import skip_unless_cms


@skip_unless_cms
@ddt.ddt
class ContainersTestCase(OpenEdxEventsTestMixin, ContentLibrariesRestApiTest):
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
    ENABLED_OPENEDX_EVENTS = [
        LIBRARY_CONTAINER_CREATED.event_type,
        LIBRARY_CONTAINER_DELETED.event_type,
        LIBRARY_CONTAINER_UPDATED.event_type,
    ]

    def test_unit_crud(self):
        """
        Test Create, Read, Update, and Delete of a Unit
        """
        lib = self._create_library(slug="containers", title="Container Test Library", description="Units and more")
        lib_key = LibraryLocatorV2.from_string(lib["id"])

        create_receiver = mock.Mock()
        LIBRARY_CONTAINER_CREATED.connect(create_receiver)

        update_receiver = mock.Mock()
        LIBRARY_CONTAINER_UPDATED.connect(update_receiver)

        delete_receiver = mock.Mock()
        LIBRARY_CONTAINER_DELETED.connect(delete_receiver)

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
        assert create_receiver.call_count == 1
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_CONTAINER_CREATED,
                "sender": None,
                "library_container": LibraryContainerData(
                    lib_key,
                    container_key="lct:CL-TEST:containers:unit:u1",
                ),
            },
            create_receiver.call_args_list[0].kwargs,
        )

        # Fetch the unit:
        unit_as_read = self._get_container(container_data["container_key"])
        # make sure it contains the same data when we read it back:
        self.assertDictContainsEntries(unit_as_read, expected_data)

        # Update the unit:
        modified_date = datetime(2024, 10, 9, 8, 7, 6, tzinfo=timezone.utc)
        with freeze_time(modified_date):
            container_data = self._update_container("lct:CL-TEST:containers:unit:u1", display_name="Unit ABC")
        expected_data['last_draft_created'] = expected_data['modified'] = '2024-10-09T08:07:06Z'
        expected_data['display_name'] = 'Unit ABC'
        self.assertDictContainsEntries(container_data, expected_data)

        assert update_receiver.call_count == 1
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_CONTAINER_UPDATED,
                "sender": None,
                "library_container": LibraryContainerData(
                    lib_key,
                    container_key="lct:CL-TEST:containers:unit:u1",
                ),
            },
            update_receiver.call_args_list[0].kwargs,
        )

        # Re-fetch the unit
        unit_as_re_read = self._get_container(container_data["container_key"])
        # make sure it contains the same data when we read it back:
        self.assertDictContainsEntries(unit_as_re_read, expected_data)

        # Delete the unit
        self._delete_container(container_data["container_key"])
        self._get_container(container_data["container_key"], expect_response=404)
        assert delete_receiver.call_count == 1
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_CONTAINER_DELETED,
                "sender": None,
                "library_container": LibraryContainerData(
                    lib_key,
                    container_key="lct:CL-TEST:containers:unit:u1",
                ),
            },
            delete_receiver.call_args_list[0].kwargs,
        )

    def test_unit_permissions(self):
        """
        Test that a regular user with read-only permissions on the library cannot create, update, or delete units.
        """
        lib = self._create_library(slug="containers2", title="Container Test Library 2", description="Unit permissions")
        container_data = self._create_container(lib["id"], "unit", slug="u2", display_name="Test Unit")

        random_user = UserFactory.create(username="Random", email="random@example.com")
        with self.as_user(random_user):
            self._create_container(lib["id"], "unit", slug="u3", display_name="Test Unit", expect_response=403)
            self._get_container(container_data["container_key"], expect_response=403)
            self._update_container(container_data["container_key"], display_name="Unit ABC", expect_response=403)
            self._delete_container(container_data["container_key"], expect_response=403)

        # Granting read-only permissions on the library should only allow retrieval, nothing else.
        self._add_user_by_email(lib["id"], random_user.email, access_level="read")
        with self.as_user(random_user):
            self._create_container(lib["id"], "unit", slug="u2", display_name="Test Unit", expect_response=403)
            self._get_container(container_data["container_key"], expect_response=200)
            self._update_container(container_data["container_key"], display_name="Unit ABC", expect_response=403)
            self._delete_container(container_data["container_key"], expect_response=403)

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

    def test_unit_add_children(self):
        """
        Test that we can add and get unit children components
        """
        update_receiver = mock.Mock()
        LIBRARY_CONTAINER_UPDATED.connect(update_receiver)
        lib = self._create_library(slug="containers", title="Container Test Library", description="Units and more")
        lib_key = LibraryLocatorV2.from_string(lib["id"])

        # Create container and add some components
        container_data = self._create_container(lib["id"], "unit", display_name="Alpha Bravo", slug=None)
        problem_block = self._add_block_to_library(lib["id"], "problem", "Problem1", can_stand_alone=False)
        html_block = self._add_block_to_library(lib["id"], "html", "Html1", can_stand_alone=False)
        self._add_container_components(
            container_data["container_key"],
            children_ids=[problem_block["id"], html_block["id"]]
        )
        data = self._get_container_components(container_data["container_key"])
        assert len(data) == 2
        assert data[0]['id'] == problem_block['id']
        assert not data[0]['can_stand_alone']
        assert data[1]['id'] == html_block['id']
        assert not data[1]['can_stand_alone']
        problem_block_2 = self._add_block_to_library(lib["id"], "problem", "Problem2", can_stand_alone=False)
        html_block_2 = self._add_block_to_library(lib["id"], "html", "Html2")
        # Add two more components
        self._add_container_components(
            container_data["container_key"],
            children_ids=[problem_block_2["id"], html_block_2["id"]]
        )
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_CONTAINER_UPDATED,
                "sender": None,
                "library_container": LibraryContainerData(
                    lib_key,
                    container_key=container_data["container_key"],
                ),
            },
            update_receiver.call_args_list[0].kwargs,
        )
        data = self._get_container_components(container_data["container_key"])
        # Verify total number of components to be 2 + 2 = 4
        assert len(data) == 4
        assert data[2]['id'] == problem_block_2['id']
        assert not data[2]['can_stand_alone']
        assert data[3]['id'] == html_block_2['id']
        assert data[3]['can_stand_alone']

    def test_unit_remove_children(self):
        """
        Test that we can remove unit children components
        """
        update_receiver = mock.Mock()
        LIBRARY_CONTAINER_UPDATED.connect(update_receiver)
        lib = self._create_library(slug="containers", title="Container Test Library", description="Units and more")
        lib_key = LibraryLocatorV2.from_string(lib["id"])

        # Create container and add some components
        container_data = self._create_container(lib["id"], "unit", display_name="Alpha Bravo", slug=None)
        problem_block = self._add_block_to_library(lib["id"], "problem", "Problem1", can_stand_alone=False)
        html_block = self._add_block_to_library(lib["id"], "html", "Html1", can_stand_alone=False)
        problem_block_2 = self._add_block_to_library(lib["id"], "problem", "Problem2", can_stand_alone=False)
        html_block_2 = self._add_block_to_library(lib["id"], "html", "Html2")
        self._add_container_components(
            container_data["container_key"],
            children_ids=[problem_block["id"], html_block["id"], problem_block_2["id"], html_block_2["id"]]
        )
        data = self._get_container_components(container_data["container_key"])
        assert len(data) == 4
        # Remove both problem blocks.
        self._remove_container_components(
            container_data["container_key"],
            children_ids=[problem_block_2["id"], problem_block["id"]]
        )
        data = self._get_container_components(container_data["container_key"])
        assert len(data) == 2
        assert data[0]['id'] == html_block['id']
        assert data[1]['id'] == html_block_2['id']
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_CONTAINER_UPDATED,
                "sender": None,
                "library_container": LibraryContainerData(
                    lib_key,
                    container_key=container_data["container_key"],
                ),
            },
            update_receiver.call_args_list[0].kwargs,
        )

    def test_unit_replace_children(self):
        """
        Test that we can completely replace/reorder unit children components.
        """
        update_receiver = mock.Mock()
        LIBRARY_CONTAINER_UPDATED.connect(update_receiver)
        lib = self._create_library(slug="containers", title="Container Test Library", description="Units and more")
        lib_key = LibraryLocatorV2.from_string(lib["id"])

        # Create container and add some components
        container_data = self._create_container(lib["id"], "unit", display_name="Alpha Bravo", slug=None)
        problem_block = self._add_block_to_library(lib["id"], "problem", "Problem1", can_stand_alone=False)
        html_block = self._add_block_to_library(lib["id"], "html", "Html1", can_stand_alone=False)
        problem_block_2 = self._add_block_to_library(lib["id"], "problem", "Problem2", can_stand_alone=False)
        html_block_2 = self._add_block_to_library(lib["id"], "html", "Html2")
        self._add_container_components(
            container_data["container_key"],
            children_ids=[problem_block["id"], html_block["id"], problem_block_2["id"], html_block_2["id"]]
        )
        data = self._get_container_components(container_data["container_key"])
        assert len(data) == 4
        assert data[0]['id'] == problem_block['id']
        assert data[1]['id'] == html_block['id']
        assert data[2]['id'] == problem_block_2['id']
        assert data[3]['id'] == html_block_2['id']

        # Reorder the components
        self._patch_container_components(
            container_data["container_key"],
            children_ids=[problem_block["id"], problem_block_2["id"], html_block["id"], html_block_2["id"]]
        )
        data = self._get_container_components(container_data["container_key"])
        assert len(data) == 4
        assert data[0]['id'] == problem_block['id']
        assert data[1]['id'] == problem_block_2['id']
        assert data[2]['id'] == html_block['id']
        assert data[3]['id'] == html_block_2['id']

        # Replace with new components
        new_problem_block = self._add_block_to_library(lib["id"], "problem", "New_Problem", can_stand_alone=False)
        new_html_block = self._add_block_to_library(lib["id"], "html", "New_Html", can_stand_alone=False)
        self._patch_container_components(
            container_data["container_key"],
            children_ids=[new_problem_block["id"], new_html_block["id"]],
        )
        data = self._get_container_components(container_data["container_key"])
        assert len(data) == 2
        assert data[0]['id'] == new_problem_block['id']
        assert data[1]['id'] == new_html_block['id']
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_CONTAINER_UPDATED,
                "sender": None,
                "library_container": LibraryContainerData(
                    lib_key,
                    container_key=container_data["container_key"],
                ),
            },
            update_receiver.call_args_list[0].kwargs,
        )
