"""
Tests for the course dates serializers.
"""

from django.utils import timezone
from edx_when.models import ContentDate, DatePolicy, UserDate

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
        self.user_date = UserDate.objects.create(
            user=self.user,
            content_date=self.content_date,
            abs_date=timezone.now())

    def test_serialization_all_fields(self):
        serializer = AllCourseDatesSerializer(self.user_date)
        data = serializer.data

        self.assertEqual(data["learner_has_access"], True)
        self.assertEqual(data["course_id"], str(self.course.id))
        self.assertEqual(data["due_date"], self.user_date.actual_date.strftime("%Y-%m-%dT%H:%M:%S%z"))
        self.assertEqual(data["assignment_title"], self.content_date.assignment_title)
        self.assertEqual(data["first_component_block_id"], self.user_date.first_component_block_id)
        self.assertEqual(data["course_name"], self.content_date.course_name)
        self.assertEqual(data["location"], str(self.user_date.location))
        self.assertEqual(data["relative"], False)
