"""
Tests for ESG Serializers
"""
from django.test import TestCase
from unittest.mock import Mock

from lms.djangoapps.ora_staff_grader.serializers import CourseMetadataSerializer, OpenResponseMetadataSerializer
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


class TestOpenResponseMetadataSerializer(TestCase):
    """
    Tests for OpenResponseMetadataSerializer
    """
    display_name = "Week 1: Time Travel Paradoxes"
    prompts = ["<p>In your own words, explain a famous time travel paradox</p>"]
    teams_enabled = False

    mock_ora_instance = None

    def setUp(self):
        self.mock_ora_instance = Mock(name='openassessment-block')
        self.mock_ora_instance.display_name = self.display_name
        self.mock_ora_instance.prompts = self.prompts
        self.mock_ora_instance.teams_enabled = self.teams_enabled

    def test_individual_ora(self):
        # An ORA with teams disabled should have type "individual"
        data = OpenResponseMetadataSerializer(self.mock_ora_instance).data

        assert data == {
            "name": self.display_name,
            "prompts": self.prompts,
            "type": "individual"
        }

    def test_team_ora(self):
        # An ORA with teams enabled should have type "team"
        self.mock_ora_instance.teams_enabled = True
        data = OpenResponseMetadataSerializer(self.mock_ora_instance).data

        assert data == {
            "name": self.display_name,
            "prompts": self.prompts,
            "type": "team"
        }
