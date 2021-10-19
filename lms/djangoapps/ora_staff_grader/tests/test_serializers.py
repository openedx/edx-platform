"""
Tests for ESG Serializers
"""
from django.test import TestCase
from unittest.mock import Mock

from lms.djangoapps.ora_staff_grader.serializers import (
    CourseMetadataSerializer,
    OpenResponseMetadataSerializer,
    SubmissionMetadataSerializer,
)
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
        super().setUp()

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
        super().setUp()

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


class TestSubmissionMetadataSerializer(TestCase):
    """
    Tests for SubmissionMetadataSerializer. Implicitly, this also exercises ScoreSerializer.

    SubmissionMetadata comes from the ORA list_staff_workflows XBlock.json_handler and has the shape:

    "<submission_uuid>": {
        "submissionUuid": uuid,
        "username": string or None,
        "teamName": string orNone,
        "dateSubmitted": string(yyyy-mm-dd HH:MM:SS),
        "dateGraded": string(yyyy-mm-dd HH:MM:SS) or None,
        "gradedBy": string or None,
        "gradingStatus": "ungraded" or "graded",
        "lockStatus": "locked", "unlocked", or "in-progress",
        "score": {} or {
            "pointsEarned": int,
            "pointsPossible": int,
        }
    }
    """
    submission_data = {
        "ungraded": {
            "submissionUuid": "ungraded",
            "username": "foo",
            "teamName": None,
            "dateSubmitted": "1969-07-16 13:32:00",
            "dateGraded": None,
            "gradedBy": None,
            "gradingStatus": "ungraded",
            "lockStatus": "unlocked",
            "score": {
                "pointsEarned": 0,
                "pointsPossible": 10
            }
        },
        "graded": {
            "submissionUuid": "graded",
            "username": "baz",
            "teamName": None,
            "dateSubmitted": "1969-07-21 21:35:00",
            "dateGraded": "1969-07-24 16:44:00",
            "gradedBy": "buz",
            "gradingStatus": "graded",
            "lockStatus": "unlocked",
            "score": {
                "pointsEarned": 9,
                "pointsPossible": 10
            }
        }
    }

    def test_submission_serialize(self):
        for submission_id, submission_data in self.submission_data.items():
            data = SubmissionMetadataSerializer(submission_data).data

            # For each submission, data is just passed through
            assert self.submission_data[submission_id] == data

    def test_missing_team_name(self):
        """
        Individual submissions may have a missing or emtpy "teamName".
        The field should be added to serialized output with null value.
        """
        submission = {
            "submissionUuid": "individual",
            "username": "Buzz",
            "dateSubmitted": "1969-07-21 21:35:00",
            "dateGraded": "1969-07-24 16:44:00",
            "gradedBy": "Houston",
            "gradingStatus": "ungraded",
            "lockStatus": "unlocked",
            "score": {
                "pointsEarned": 10,
                "pointsPossible": 10
            }
        }

        expected_output = {
            "submissionUuid": "individual",
            "username": "Buzz",
            "teamName": None,
            "dateSubmitted": "1969-07-21 21:35:00",
            "dateGraded": "1969-07-24 16:44:00",
            "gradedBy": "Houston",
            "gradingStatus": "ungraded",
            "lockStatus": "unlocked",
            "score": {
                "pointsEarned": 10,
                "pointsPossible": 10
            }
        }

        data = SubmissionMetadataSerializer(submission).data

        assert data == expected_output

    def test_empty_score(self):
        """
        An empty score dict should be serialized as None
        """
        submission = {
            "submissionUuid": "empty-score",
            "username": "WOPR",
            "dateSubmitted": "1983-06-03 00:00:00",
            "dateGraded": None,
            "gradedBy": None,
            "gradingStatus": "ungraded",
            "lockStatus": "unlocked",
            "score": {}
        }

        expected_output = {
            "submissionUuid": "empty-score",
            "username": "WOPR",
            "teamName": None,
            "dateSubmitted": "1983-06-03 00:00:00",
            "dateGraded": None,
            "gradedBy": None,
            "gradingStatus": "ungraded",
            "lockStatus": "unlocked",
            "score": None
        }

        data = SubmissionMetadataSerializer(submission).data

        assert data == expected_output
