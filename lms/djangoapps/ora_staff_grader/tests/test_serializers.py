"""
Tests for ESG Serializers
"""
from lms.djangoapps.ora_staff_grader.serializers import CourseMetadataSerializer
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


class TestCourseMetadataSerializer(SharedModuleStoreTestCase):
    """
    Tests for CourseMetadataSerializer
    """
    course_org = "Oxford"
    course_name = "Introduction to Time Travel"
    course_number = "TT101"
    course_run = "2054"
    course_id = "course-v1:Oxford+TT101+2054"

    def setUp(self):
        self.course_overview = CourseOverviewFactory.create(
            org=self.course_org,
            display_name=self.course_name,
            display_number_with_default=self.course_number,
            run=self.course_run,
        )

    def test_course_serialize(self):
        data = CourseMetadataSerializer(self.course_overview).data

        assert data == {
            "title": self.course_name,
            "org": self.course_org,
            "number": self.course_number,
            "courseId": self.course_id,
        }
