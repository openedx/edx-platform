"""
Unit tests for the vertical block.
"""
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
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
        self.assertEqual(response.status_code, 404)


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

        expected_response = [
            {
                "name": self.html_unit_first.display_name_with_default,
                "block_id": str(self.html_unit_first.location),
            },
            {
                "name": self.html_unit_second.display_name_with_default,
                "block_id": str(self.html_unit_second.location),
            },
        ]
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
        self.assertEqual(response.status_code, 404)
