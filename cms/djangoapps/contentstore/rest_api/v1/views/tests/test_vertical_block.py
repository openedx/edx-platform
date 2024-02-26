"""
Unit tests for the vertical block.
"""
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import BlockFactory  # lint-amnesty, pylint: disable=wrong-import-order


class ContainerHandlerViewTest(CourseTestCase):
    """
    Unit tests for the ContainerHandlerView.
    """

    def setUp(self):
        super().setUp()
        self.chapter = BlockFactory.create(
            parent=self.course, category="chapter", display_name="Week 1"
        )
        self.sequential = BlockFactory.create(
            parent=self.chapter, category="sequential", display_name="Lesson 1"
        )
        self.vertical = self._create_block(self.sequential, "vertical", "Unit")

        self.store = modulestore()
        self.store.publish(self.vertical.location, self.user.id)

    def _get_reverse_url(self, location):
        """
        Creates url to current handler view api
        """
        return reverse(
            "cms.djangoapps.contentstore:v1:container_handler",
            kwargs={"usage_key_string": location},
        )

    def _create_block(self, parent, category, display_name, **kwargs):
        """
        Creates a block without publishing it.
        """
        return BlockFactory.create(
            parent=parent,
            category=category,
            display_name=display_name,
            publish_item=False,
            user_id=self.user.id,
            **kwargs
        )

    def test_success_response(self):
        """
        Check that endpoint is valid and success response.
        """
        url = self._get_reverse_url(self.vertical.location)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_valid_usage_key_string(self):
        """
        Check that invalid 'usage_key_string' raises Http404.
        """
        usage_key_string = "i4x://InvalidOrg/InvalidCourse/vertical/static/InvalidContent"
        url = self._get_reverse_url(usage_key_string)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
