"""
Tests for ESG Serializers
"""
from django.test import TestCase
from unittest.mock import Mock

from lms.djangoapps.ora_staff_grader.serializers import (
    CourseMetadataSerializer,
    InitializeSerializer,
    OpenResponseMetadataSerializer,
)
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


class TestCourseMetadataSerializer(SharedModuleStoreTestCase):
    """
    Tests for CourseMetadataSerializer
    """
    course_data = {
        "org": "Oxford",
        "display_name": "Introduction to Time Travel",
        "display_number_with_default": "TT101",
        "run": "2054",
    }

    course_id = "course-v1:Oxford+TT101+2054"

    def setUp(self):
        super().setUp()

        self.course_overview = CourseOverviewFactory.create(**self.course_data)

    def test_course_serialize(self):
        data = CourseMetadataSerializer(self.course_overview).data

        assert data == {
            "title": self.course_data["display_name"],
            "org": self.course_data["org"],
            "number": self.course_data["display_number_with_default"],
            "courseId": self.course_id,
        }


class TestOpenResponseMetadataSerializer(TestCase):
    """
    Tests for OpenResponseMetadataSerializer
    """
    ora_data = {
        "display_name": "Week 1: Time Travel Paradoxes",
        "prompts": ["<p>In your own words, explain a famous time travel paradox</p>"],
        "teams_enabled": False
    }

    def setUp(self):
        super().setUp()

        self.mock_ora_instance = Mock(name='openassessment-block', **self.ora_data)

    def test_individual_ora(self):
        # An ORA with teams disabled should have type "individual"
        data = OpenResponseMetadataSerializer(self.mock_ora_instance).data

        assert data == {
            "name": self.ora_data['display_name'],
            "prompts": self.ora_data['prompts'],
            "type": "individual",
        }

    def test_team_ora(self):
        # An ORA with teams enabled should have type "team"
        self.mock_ora_instance.teams_enabled = True
        data = OpenResponseMetadataSerializer(self.mock_ora_instance).data

        assert data == {
            "name": self.ora_data['display_name'],
            "prompts": self.ora_data['prompts'],
            "type": "team",
        }


class TestInitializeSerializer(TestCase):
    """
    Tests for InitializeSerializer
    """
    def set_up_ora(self):
        """ Create a mock Open Repsponse Assessment for serialization """
        ora_data = {
            "display_name": "Week 1: Time Travel Paradoxes",
            "prompts": ["<p>In your own words, explain a famous time travel paradox</p>"],
            "teams_enabled": False
        }

        return Mock(name='openassessment-block', **ora_data)

    def set_up_course_metadata(self):
        course_org = "Oxford"
        course_name = "Introduction to Time Travel"
        course_number = "TT101"
        course_run = "2054"
        course_id = "course-v1:Oxford+TT101+2054"

        return CourseOverviewFactory.create(
            org=course_org,
            display_name=course_name,
            display_number_with_default=course_number,
            run=course_run,
        )

    def setUp(self):
        super().setUp()

        self.mock_ora_instance = self.set_up_ora()
        self.mock_course_metadata = self.set_up_course_metadata()

        # Submissions data gets some minor transforms
        # This test data does not undergo any transforms so we can do easier comparison tests
        self.mock_submissions_data = {
            "space-oddity": {
                "submissionUuid": "space-oddity",
                "username": "Major Tom",
                "teamName": None,
                "dateSubmitted": "1969-06-20 00:00:00",
                "dateGraded": "1969-07-11 00:00:00",
                "gradedBy": "Ground Control",
                "gradingStatus": "graded",
                "lockStatus": "unlocked",
                "score": {
                    "pointsEarned": 10,
                    "pointsPossible": 10,
                }
            }
        }

        # Rubric data is passed through without transforms, we can create a toy response
        self.mock_rubric_data = {"foo": "bar"}

    def test_serializer_shape(self):
        """ Simplest test, is the structure correct? """
        input_data = {
            "courseMetadata": self.mock_course_metadata,
            "oraMetadata": self.mock_ora_instance,
            "submissions": self.mock_submissions_data,
            "rubricConfig": self.mock_rubric_data,
        }

        output_data = InitializeSerializer(input_data).data

        assert output_data.keys() == input_data.keys()

    def test_serializer_output(self):
        input_data = {
            "courseMetadata": self.mock_course_metadata,
            "oraMetadata": self.mock_ora_instance,
            "submissions": self.mock_submissions_data,
            "rubricConfig": self.mock_rubric_data,
        }

        output_data = InitializeSerializer(input_data).data

        # Check that each of the sub-serializers assembles data correctly
        assert output_data['courseMetadata'] == CourseMetadataSerializer(self.mock_course_metadata).data
        assert output_data['oraMetadata'] == OpenResponseMetadataSerializer(self.mock_ora_instance).data
        assert output_data['submissions'] == self.mock_submissions_data
        assert output_data['rubricConfig'] == self.mock_rubric_data

    def test_submissions_transforms(self):
        """
        Submissions get special transforms to deal with empty/missing fields:
        - teamName/username are added if omitted, with a value of None
        - Empty score dict is replaced with None
        """
        submission_data = {
            "submissionUuid": "empty_fields_test",
            "username": "WOPR",
            "dateSubmitted": "1983-06-03 00:00:00",
            "dateGraded": None,
            "gradedBy": None,
            "gradingStatus": "ungraded",
            "lockStatus": "unlocked",
            "score": {}
        }

        expected_submission_transform = {
            "submissionUuid": "empty_fields_test",
            "username": "WOPR",
            "teamName": None,
            "dateSubmitted": "1983-06-03 00:00:00",
            "dateGraded": None,
            "gradedBy": None,
            "gradingStatus": "ungraded",
            "lockStatus": "unlocked",
            "score": None
        }

        transformed_submission = InitializeSerializer.transform_submission(submission_data)

        assert transformed_submission == expected_submission_transform
