"""
Tests for the course dates serializers.
"""

from django.db.models import F, Value
from django.utils import timezone
from edx_when.models import ContentDate, DatePolicy

from lms.djangoapps.mobile_api.course_dates.serializers import ContentDateSerializer
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase


class TestContentDateSerializer(MixedSplitTestCase):
    """
    Tests for the ContentDateSerializer.
    """

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

    def test_content_date_serializer(self):
        """
        Test the serializer for ContentDate model.
        """
        queryset = ContentDate.objects.annotate(
            due_date=F("policy__abs_date"),
            course_name=Value("Test Display Name"),
        ).first()
        serializer = ContentDateSerializer(queryset)
        expected_data = {
            "course_id": str(self.course.id),
            "assignment_block_id": str(self.sequential.location),
            "due_date": str(self.date_policy.abs_date),
            "assignment_title": self.sequential.display_name,
            "learner_has_access": True,
            "course_name": "Test Display Name",
        }

        self.assertEqual(serializer.data, expected_data)
