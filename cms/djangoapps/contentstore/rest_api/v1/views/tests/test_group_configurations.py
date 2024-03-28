"""
Unit tests for the course's setting group configuration.
"""
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.course_group_config import (
    CONTENT_GROUP_CONFIGURATION_NAME,
)
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from xmodule.partitions.partitions import (
    Group,
    UserPartition,
)  # lint-amnesty, pylint: disable=wrong-import-order

from ...mixins import PermissionAccessMixin


class CourseGroupConfigurationsViewTest(CourseTestCase, PermissionAccessMixin):
    """
    Tests for CourseGroupConfigurationsView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "cms.djangoapps.contentstore:v1:group_configurations",
            kwargs={"course_id": self.course.id},
        )

    def test_success_response(self):
        """
        Check that endpoint is valid and success response.
        """
        self.course.user_partitions = [
            UserPartition(
                0,
                "First name",
                "First description",
                [Group(0, "Group A"), Group(1, "Group B"), Group(2, "Group C")],
            ),  # lint-amnesty, pylint: disable=line-too-long
        ]
        self.save_course()

        if "split_test" not in self.course.advanced_modules:
            self.course.advanced_modules.append("split_test")
            self.store.update_item(self.course, self.user.id)

        response = self.client.get(self.url)
        self.assertEqual(len(response.data["all_group_configurations"]), 1)
        self.assertEqual(len(response.data["experiment_group_configurations"]), 1)
        self.assertContains(response, "First name", count=1)
        self.assertContains(response, "Group C")
        self.assertContains(response, CONTENT_GROUP_CONFIGURATION_NAME)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
