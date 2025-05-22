"""
Tests for Learning-Core-based Content Libraries
"""
from datetime import datetime, timezone

import ddt
from freezegun import freeze_time

from opaque_keys.edx.locator import LibraryLocatorV2

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content_libraries import api
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

    def setUp(self):
        super().setUp()
        self.create_date = datetime(2024, 9, 8, 7, 6, 5, tzinfo=timezone.utc)
        self.lib = self._create_library(slug="containers", title="Container Test Library", description="Units and more")
        self.lib_key = LibraryLocatorV2.from_string(self.lib["id"])

        # Create containers
        with freeze_time(self.create_date):
            # Unit
            self.unit = self._create_container(self.lib["id"], "unit", display_name="Alpha Bravo", slug=None)
            self.unit_with_components = self._create_container(
                self.lib["id"],
                "unit",
                display_name="Alpha Charly",
                slug=None,
            )
            # Subsection
            self.subsection = self._create_container(self.lib["id"], "subsection", display_name="Subsection Alpha", slug=None)
            # Section
            self.section = self._create_container(self.lib["id"], "section", display_name="Section Alpha", slug=None)

        # Create blocks
        self.problem_block = self._add_block_to_library(self.lib["id"], "problem", "Problem1", can_stand_alone=False)
        self.html_block = self._add_block_to_library(self.lib["id"], "html", "Html1", can_stand_alone=False)
        self.problem_block_2 = self._add_block_to_library(self.lib["id"], "problem", "Problem2", can_stand_alone=False)
        self.html_block_2 = self._add_block_to_library(self.lib["id"], "html", "Html2")

        # Add components to `unit_with_components`
        self._add_container_components(
            self.unit_with_components["id"],
            children_ids=[
                self.problem_block["id"],
                self.html_block["id"],
                self.problem_block_2["id"],
                self.html_block_2["id"],
            ]
        )

    @ddt.data(
        ("unit", "u1", "Test Unit"),
        ("subsection", "subs1", "Test Subsection"),
        ("section", "s1", "Test Section"),
    )
    @ddt.unpack
    def test_container_crud(self, container_type, slug, display_name):
        """
        Test Create, Read, Update, and Delete of a Containers
        """
        # Create container:
        create_date = datetime(2024, 9, 8, 7, 6, 5, tzinfo=timezone.utc)
        with freeze_time(create_date):
            container_data = self._create_container(
                self.lib["id"],
                container_type,
                slug=slug,
                display_name=display_name
        )
        id = f"lct:CL-TEST:containers:{container_type}:{slug}"
        expected_data = {
            "id": id,
            "container_type": container_type,
            "display_name": display_name,
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

        # Fetch the container:
        container_as_read = self._get_container(container_data["id"])
        # make sure it contains the same data when we read it back:
        self.assertDictContainsEntries(container_as_read, expected_data)

        # Update the container:
        modified_date = datetime(2024, 10, 9, 8, 7, 6, tzinfo=timezone.utc)
        with freeze_time(modified_date):
            container_data = self._update_container(id, display_name=f"New Display Name for {container_type}")
        expected_data["last_draft_created"] = expected_data["modified"] = "2024-10-09T08:07:06Z"
        expected_data["display_name"] = f"New Display Name for {container_type}"
        self.assertDictContainsEntries(container_data, expected_data)

        # Re-fetch the container
        container_as_re_read = self._get_container(container_data["id"])
        # make sure it contains the same data when we read it back:
        self.assertDictContainsEntries(container_as_re_read, expected_data)

        # Delete the container
        self._delete_container(container_data["id"])
        self._get_container(container_data["id"], expect_response=404)

    @ddt.data(
        ("unit", "u2", "Test Unit"),
        ("subsection", "subs2", "Test Subsection"),
        ("section", "s2", "Test Section"),
    )
    @ddt.unpack
    def test_container_permissions(self, container_type, slug, display_name):
        """
        Test that a regular user with read-only permissions on the library cannot create, update, or delete containers.
        """
        container_data = self._create_container(self.lib["id"], container_type, slug=slug, display_name=display_name)

        random_user = UserFactory.create(username="Random", email="random@example.com")
        with self.as_user(random_user):
            self._create_container(self.lib["id"], container_type, slug="new_slug", display_name=display_name, expect_response=403)
            self._get_container(container_data["id"], expect_response=403)
            self._update_container(container_data["id"], display_name="New Display Name", expect_response=403)
            self._delete_container(container_data["id"], expect_response=403)

        # Granting read-only permissions on the library should only allow retrieval, nothing else.
        self._add_user_by_email(self.lib["id"], random_user.email, access_level="read")
        with self.as_user(random_user):
            self._create_container(self.lib["id"], container_type, slug=slug, display_name=display_name, expect_response=403)
            self._get_container(container_data["id"], expect_response=200)
            self._update_container(container_data["id"], display_name="New Display Name", expect_response=403)
            self._delete_container(container_data["id"], expect_response=403)

    @ddt.data(
        ("unit", "Alpha Bravo", "lct:CL-TEST:containers:unit:alpha-bravo-"),
        ("subsection", "Subsection Alpha", "lct:CL-TEST:containers:subsection:subsection-alpha-"),
        ("section", "Section Alpha", "lct:CL-TEST:containers:section:section-alpha-"),
    )
    @ddt.unpack
    def test_containers_gets_auto_slugs(self, container_type, display_name, expected_id):
        """
        Test that we can create containers by specifying only a title, and they get
        unique slugs assigned automatically.
        """
        container_1 = getattr(self, container_type)
        container_2 = self._create_container(self.lib["id"], container_type, display_name=display_name, slug=None)

        assert container_1["id"].startswith(expected_id)
        assert container_2["id"].startswith(expected_id)
        assert container_1["id"] != container_2["id"]

    def test_unit_add_children(self):
        """
        Test that we can add and get unit children components
        """
        # Create container and add some components
        self._add_container_components(
            self.unit["id"],
            children_ids=[self.problem_block["id"], self.html_block["id"]]
        )
        data = self._get_container_components(self.unit["id"])
        assert len(data) == 2
        assert data[0]['id'] == self.problem_block['id']
        assert not data[0]['can_stand_alone']
        assert data[1]['id'] == self.html_block['id']
        assert not data[1]['can_stand_alone']
        problem_block_2 = self._add_block_to_library(self.lib["id"], "problem", "Problem_2", can_stand_alone=False)
        html_block_2 = self._add_block_to_library(self.lib["id"], "html", "Html_2")
        # Add two more components
        self._add_container_components(
            self.unit["id"],
            children_ids=[problem_block_2["id"], html_block_2["id"]]
        )
        data = self._get_container_components(self.unit["id"])
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
        data = self._get_container_components(self.unit_with_components["id"])
        assert len(data) == 4
        # Remove both problem blocks.
        self._remove_container_components(
            self.unit_with_components["id"],
            children_ids=[self.problem_block_2["id"], self.problem_block["id"]]
        )
        data = self._get_container_components(self.unit_with_components["id"])
        assert len(data) == 2
        assert data[0]['id'] == self.html_block['id']
        assert data[1]['id'] == self.html_block_2['id']

    def test_unit_replace_children(self):
        """
        Test that we can completely replace/reorder unit children components.
        """
        data = self._get_container_components(self.unit_with_components["id"])
        assert len(data) == 4
        assert data[0]['id'] == self.problem_block['id']
        assert data[1]['id'] == self.html_block['id']
        assert data[2]['id'] == self.problem_block_2['id']
        assert data[3]['id'] == self.html_block_2['id']

        # Reorder the components
        self._patch_container_components(
            self.unit_with_components["id"],
            children_ids=[
                self.problem_block["id"],
                self.problem_block_2["id"],
                self.html_block["id"],
                self.html_block_2["id"],
            ]
        )
        data = self._get_container_components(self.unit_with_components["id"])
        assert len(data) == 4
        assert data[0]['id'] == self.problem_block['id']
        assert data[1]['id'] == self.problem_block_2['id']
        assert data[2]['id'] == self.html_block['id']
        assert data[3]['id'] == self.html_block_2['id']

        # Replace with new components
        new_problem_block = self._add_block_to_library(self.lib["id"], "problem", "New_Problem", can_stand_alone=False)
        new_html_block = self._add_block_to_library(self.lib["id"], "html", "New_Html", can_stand_alone=False)
        self._patch_container_components(
            self.unit_with_components["id"],
            children_ids=[new_problem_block["id"], new_html_block["id"]],
        )
        data = self._get_container_components(self.unit_with_components["id"])
        assert len(data) == 2
        assert data[0]['id'] == new_problem_block['id']
        assert data[1]['id'] == new_html_block['id']

    @ddt.data(
        "unit",
        "subsection",
        "section",
    )
    def test_restore_containers(self, container_type):
        """
        Test restore a deleted container.
        """
        container = getattr(self, container_type)

        # Delete container
        self._delete_container(container["id"])

        # Restore container
        self._restore_container(container["id"])
        new_container_data = self._get_container(container["id"])
        expected_data = {
            "id": container["id"],
            "container_type": container_type,
            "display_name": container["display_name"],
            "last_published": None,
            "published_by": "",
            "last_draft_created": "2024-09-08T07:06:05Z",
            "last_draft_created_by": 'Bob',
            'has_unpublished_changes': True,
            'created': '2024-09-08T07:06:05Z',
            'modified': '2024-09-08T07:06:05Z',
            'collections': [],
        }

        self.assertDictContainsEntries(new_container_data, expected_data)

    def test_container_collections(self):
        # Create a collection
        col1 = api.create_library_collection(
            self.lib_key,
            "COL1",
            title="Collection 1",
            created_by=self.user.id,
            description="Description for Collection 1",
        )

        result = self._patch_container_collections(
            self.unit["id"],
            collection_keys=[col1.key],
        )

        assert result['count'] == 1

        # Fetch the unit
        unit_as_read = self._get_container(self.unit["id"])

        # Verify the collections
        assert unit_as_read['collections'] == [{"title": col1.title, "key": col1.key}]

    def test_publish_container(self):  # pylint: disable=too-many-statements
        """
        Test that we can publish the changes to a specific container
        """
        html_block_3 = self._add_block_to_library(self.lib["id"], "html", "Html3")
        self._add_container_components(
            self.unit["id"],
            children_ids=[
                self.html_block["id"],
                html_block_3["id"],
            ]
        )

        # At first everything is unpublished:
        c1_before = self._get_container(self.unit_with_components["id"])
        assert c1_before["has_unpublished_changes"]
        c1_components_before = self._get_container_components(self.unit_with_components["id"])
        assert len(c1_components_before) == 4
        assert c1_components_before[0]["id"] == self.problem_block["id"]
        assert c1_components_before[0]["has_unpublished_changes"]
        assert c1_components_before[0]["published_by"] is None
        assert c1_components_before[1]["id"] == self.html_block["id"]
        assert c1_components_before[1]["has_unpublished_changes"]
        assert c1_components_before[1]["published_by"] is None
        assert c1_components_before[2]["id"] == self.problem_block_2["id"]
        assert c1_components_before[2]["has_unpublished_changes"]
        assert c1_components_before[2]["published_by"] is None
        assert c1_components_before[3]["id"] == self.html_block_2["id"]
        assert c1_components_before[3]["has_unpublished_changes"]
        assert c1_components_before[3]["published_by"] is None
        c2_before = self._get_container(self.unit["id"])
        assert c2_before["has_unpublished_changes"]

        # Now publish only Container 1
        self._publish_container(self.unit_with_components["id"])

        # Now it is published:
        c1_after = self._get_container(self.unit_with_components["id"])
        assert c1_after["has_unpublished_changes"] is False
        c1_components_after = self._get_container_components(self.unit_with_components["id"])
        assert len(c1_components_after) == 4
        assert c1_components_after[0]["id"] == self.problem_block["id"]
        assert c1_components_after[0]["has_unpublished_changes"] is False
        assert c1_components_after[0]["published_by"] == self.user.username
        assert c1_components_after[1]["id"] == self.html_block["id"]
        assert c1_components_after[1]["has_unpublished_changes"] is False
        assert c1_components_after[1]["published_by"] == self.user.username
        assert c1_components_after[2]["id"] == self.problem_block_2["id"]
        assert c1_components_after[2]["has_unpublished_changes"] is False
        assert c1_components_after[2]["published_by"] == self.user.username
        assert c1_components_after[3]["id"] == self.html_block_2["id"]
        assert c1_components_after[3]["has_unpublished_changes"] is False
        assert c1_components_after[3]["published_by"] == self.user.username

        # and container 2 is still unpublished, except for the shared HTML block that is also in container 1:
        c2_after = self._get_container(self.unit["id"])
        assert c2_after["has_unpublished_changes"]
        c2_components_after = self._get_container_components(self.unit["id"])
        assert len(c2_components_after) == 2
        assert c2_components_after[0]["id"] == self.html_block["id"]
        assert c2_components_after[0]["has_unpublished_changes"] is False  # published since it's also in container 1
        assert c2_components_after[0]["published_by"] == self.user.username
        assert c2_components_after[1]["id"] == html_block_3["id"]
        assert c2_components_after[1]["has_unpublished_changes"]  # unaffected
        assert c2_components_after[1]["published_by"] is None
