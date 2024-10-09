"""
Unit tests for the vertical block.
"""

from django.urls import reverse
from rest_framework import status
from edx_toggles.toggles.testutils import override_waffle_flag
from xblock.validation import ValidationMessage

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from openedx.core.djangoapps.content_tagging.toggles import DISABLE_TAGGING_FEATURE
from xmodule.partitions.partitions import (
    ENROLLMENT_TRACK_PARTITION_ID,
    Group,
    UserPartition,
)
from xmodule.modulestore.django import (
    modulestore,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import (
    BlockFactory,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore import (
    ModuleStoreEnum,
)  # lint-amnesty, pylint: disable=wrong-import-order


class BaseXBlockContainer(CourseTestCase):
    """
    Base xBlock container handler.

    Contains common function for processing course xblocks.
    """

    view_name = None

    def setUp(self):
        super().setUp()
        self.store = modulestore()
        self.setup_xblock()

    def setup_xblock(self):
        """
        Set up XBlock objects for testing purposes.

        This method creates XBlock objects representing a course structure with chapters,
        sequentials, verticals and others.
        """
        self.chapter = self.create_block(
            parent=self.course.location,
            category="chapter",
            display_name="Week 1",
        )

        self.sequential = self.create_block(
            parent=self.chapter.location,
            category="sequential",
            display_name="Lesson 1",
        )

        self.vertical = self.create_block(self.sequential.location, "vertical", "Unit")

        self.html_unit_first = self.create_block(
            parent=self.vertical.location,
            category="html",
            display_name="Html Content 1",
        )

        self.html_unit_second = self.create_block(
            parent=self.vertical.location,
            category="html",
            display_name="Html Content 2",
            upstream="lb:FakeOrg:FakeLib:html:FakeBlock",
            upstream_version=5,
        )

    def create_block(self, parent, category, display_name, **kwargs):
        """
        Creates a block without publishing it.
        """
        return BlockFactory.create(
            parent_location=parent,
            category=category,
            display_name=display_name,
            modulestore=self.store,
            publish_item=False,
            user_id=self.user.id,
            **kwargs,
        )

    def get_reverse_url(self, location):
        """
        Creates url to current view api name
        """
        return reverse(
            f"cms.djangoapps.contentstore:v1:{self.view_name}",
            kwargs={"usage_key_string": location},
        )

    def publish_item(self, store, item_location):
        """
        Publish the item at the given location
        """
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            store.publish(item_location, ModuleStoreEnum.UserID.test)

    def set_group_access(self, xblock, value):
        """
        Sets group_access to specified value and calls update_item to persist the change.
        """
        xblock.group_access = value
        self.store.update_item(xblock, self.user.id)


class ContainerHandlerViewTest(BaseXBlockContainer):
    """
    Unit tests for the ContainerHandlerView.
    """

    view_name = "container_handler"

    def test_success_response(self):
        """
        Check that endpoint is valid and success response.
        """
        url = self.get_reverse_url(self.vertical.location)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_valid_usage_key_string(self):
        """
        Check that invalid 'usage_key_string' raises Http404.
        """
        usage_key_string = (
            "i4x://InvalidOrg/InvalidCourse/vertical/static/InvalidContent"
        )
        url = self.get_reverse_url(usage_key_string)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ContainerVerticalViewTest(BaseXBlockContainer):
    """
    Unit tests for the ContainerVerticalViewTest.
    """

    view_name = "container_vertical"

    def test_success_response(self):
        """
        Check that endpoint returns valid response data.
        """
        url = self.get_reverse_url(self.vertical.location)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["children"]), 2)
        self.assertFalse(response.data["is_published"])
        self.assertTrue(response.data["can_paste_component"])

    def test_xblock_is_published(self):
        """
        Check that published xBlock container returns.
        """
        self.publish_item(self.store, self.vertical.location)
        url = self.get_reverse_url(self.vertical.location)
        response = self.client.get(url)
        self.assertTrue(response.data["is_published"])

    def test_children_content(self):
        """
        Check that returns valid response with children of vertical container.
        """
        url = self.get_reverse_url(self.vertical.location)
        response = self.client.get(url)

        expected_user_partition_info = {
            "selectable_partitions": [],
            "selected_partition_index": -1,
            "selected_groups_label": "",
        }

        expected_user_partitions = [
            {
                "id": ENROLLMENT_TRACK_PARTITION_ID,
                "name": "Enrollment Track Groups",
                "scheme": "enrollment_track",
                "groups": [
                    {"id": 1, "name": "Audit", "selected": False, "deleted": False}
                ],
            }
        ]

        expected_response = [
            {
                "name": self.html_unit_first.display_name_with_default,
                "block_id": str(self.html_unit_first.location),
                "block_type": self.html_unit_first.location.block_type,
                "upstream_link": None,
                "user_partition_info": expected_user_partition_info,
                "user_partitions": expected_user_partitions,
                "actions": {
                    "can_copy": True,
                    "can_duplicate": True,
                    "can_move": True,
                    "can_manage_access": True,
                    "can_delete": True,
                    "can_manage_tags": True,
                },
                "validation_messages": [],
                "render_error": "",
            },
            {
                "name": self.html_unit_second.display_name_with_default,
                "block_id": str(self.html_unit_second.location),
                "block_type": self.html_unit_second.location.block_type,
                "actions": {
                    "can_copy": True,
                    "can_duplicate": True,
                    "can_move": True,
                    "can_manage_access": True,
                    "can_delete": True,
                    "can_manage_tags": True,
                },
                "upstream_link": {
                    "upstream_ref": "lb:FakeOrg:FakeLib:html:FakeBlock",
                    "version_synced": 5,
                    "version_available": None,
                    "version_declined": None,
                    "error_message": "Linked library item was not found in the system",
                    "ready_to_sync": False,
                },
                "user_partition_info": expected_user_partition_info,
                "user_partitions": expected_user_partitions,
                "validation_messages": [],
                "render_error": "",
            },
        ]
        self.maxDiff = None
        self.assertEqual(response.data["children"], expected_response)

    def test_not_valid_usage_key_string(self):
        """
        Check that invalid 'usage_key_string' raises Http404.
        """
        usage_key_string = (
            "i4x://InvalidOrg/InvalidCourse/vertical/static/InvalidContent"
        )
        url = self.get_reverse_url(usage_key_string)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_waffle_flag(DISABLE_TAGGING_FEATURE, True)
    def test_actions_with_turned_off_taxonomy_flag(self):
        """
        Check that action manage_tags for each child item has the same value as taxonomy flag.
        """
        url = self.get_reverse_url(self.vertical.location)
        response = self.client.get(url)
        for children in response.data["children"]:
            self.assertFalse(children["actions"]["can_manage_tags"])

    def test_validation_errors(self):
        """
        Check that child has an error.
        """
        self.course.user_partitions = [
            UserPartition(
                0,
                "first_partition",
                "Test Partition",
                [Group("0", "alpha"), Group("1", "beta")],
            ),
        ]
        self.store.update_item(self.course, self.user.id)

        user_partition = self.course.user_partitions[0]
        vertical = self.store.get_item(self.vertical.location)
        html_unit_first = self.store.get_item(self.html_unit_first.location)

        group_first = user_partition.groups[0]
        group_second = user_partition.groups[1]

        # Set access settings so html will contradict vertical
        self.set_group_access(vertical, {user_partition.id: [group_second.id]})
        self.set_group_access(html_unit_first, {user_partition.id: [group_first.id]})

        # update vertical/html
        vertical = self.store.get_item(self.vertical.location)
        html_unit_first = self.store.get_item(self.html_unit_first.location)

        url = self.get_reverse_url(self.vertical.location)
        response = self.client.get(url)
        children_response = response.data["children"]

        # Verify that html_unit_first access settings contradict its parent's access settings.
        self.assertEqual(children_response[0]["validation_messages"][0]["type"], ValidationMessage.ERROR)

        # Verify that html_unit_second has no validation messages.
        self.assertFalse(children_response[1]["validation_messages"])
