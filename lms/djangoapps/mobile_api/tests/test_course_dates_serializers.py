"""
Tests for the course dates serializers.
"""

from unittest.mock import patch

from django.db.models import F, Value
from django.utils import timezone
from edx_when.models import ContentDate, DatePolicy

from lms.djangoapps.mobile_api.course_dates.serializers import AllCourseDatesSerializer
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase


class TestAllCourseDatesSerializer(MixedSplitTestCase):
    """
    Tests for the AllCourseDatesSerializer.
    """

    CREATE_USER = True

    def setUp(self):
        """
        Set up the test cases.
        """
        super().setUp()

        self.course = CourseFactory.create(modulestore=self.store)
        self.course_overview = CourseOverviewFactory.create(id=self.course.id, display_name="Test Display Name")
        self.chapter = self.make_block("chapter", self.course)
        self.sequential = self.make_block("sequential", self.chapter)

        self.date_policy = DatePolicy.objects.create(
            abs_date=timezone.now(),
        )
        self.content_date = ContentDate.objects.create(
            course_id=self.course.id,
            location=self.sequential.location,
            active=True,
            block_type="sequential",
            field="due",
            policy=self.date_policy,
        )

    @patch("lms.djangoapps.mobile_api.course_dates.serializers.get_current_user")
    def test_content_date_serializer(self, mock_get_current_user):
        """
        Test the serializer for ContentDate model.
        """
        mock_get_current_user.return_value = self.user
        queryset = ContentDate.objects.annotate(
            due_date=F("policy__abs_date"),
            course_name=Value("Test Display Name"),
            relative=Value(True),
        ).first()
        serializer = AllCourseDatesSerializer(queryset)
        expected_data = {
            "course_id": str(self.course.id),
            "location": str(self.sequential.location),
            "due_date": self.date_policy.abs_date.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "assignment_title": self.sequential.display_name,
            "learner_has_access": True,
            "course_name": "Test Display Name",
            "relative": True,
            "first_component_block_id": None,
        }

        self.assertEqual(serializer.data, expected_data)
