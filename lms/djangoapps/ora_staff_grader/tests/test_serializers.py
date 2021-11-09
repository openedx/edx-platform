"""
Tests for ESG Serializers
"""
import ddt
from django.test import TestCase
from unittest.mock import Mock, MagicMock

from lms.djangoapps.ora_staff_grader.serializers import (
    AssessmentCriteriaSerializer,
    CourseMetadataSerializer,
    GradeDataSerializer,
    InitializeSerializer,
    OpenResponseMetadataSerializer,
    ResponseSerializer,
    ScoreField,
    ScoreSerializer,
    SubmissionDetailResponseSerializer,
    SubmissionMetadataSerializer,
    UploadedFileSerializer,
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


class TestSubmissionMetadataSerializer(TestCase):
    """
    Tests for SubmissionMetadataSerializer. Implicitly, this also exercises ScoreSerializer.
    SubmissionMetadata comes from the ORA list_staff_workflows XBlock.json_handler and has the shape:
    "<submission_uuid>": {
        "submissionUuid": "<submission_uuid>",
        "username": "<username/empty>",
        "teamName": "<team_name/empty>",
        "dateSubmitted": "<yyyy-mm-dd HH:MM:SS>",
        "dateGraded": "<yyyy-mm-dd HH:MM:SS/None>",
        "gradedBy": "<username/empty>",
        "gradingStatus": "<ungraded/graded>",
        "lockStatus": "<locked/unlocked/in-progress",
        "score": {
            "pointsEarned": <num>,
            "pointsPossible": <num>
        }
    }
    Right now, this is just passed through without any transforms.
    """
    submission_data = {
        "a": {
            "submissionUuid": "a",
            "username": "foo",
            "teamName": "",
            "dateSubmitted": "1969-07-16 13:32:00",
            "dateGraded": "None",
            "gradedBy": "",
            "gradingStatus": "ungraded",
            "lockStatus": "unlocked",
            "score": {
                "pointsEarned": 0,
                "pointsPossible": 10
            }
        },
        "b": {
            "submissionUuid": "b",
            "username": "",
            "teamName": "bar",
            "dateSubmitted": "1969-07-20 20:17:40",
            "dateGraded": "None",
            "gradedBy": "",
            "gradingStatus": "ungraded",
            "lockStatus": "in-progress",
            "score": {
                "pointsEarned": 0,
                "pointsPossible": 10
            }
        },
        "c": {
            "submissionUuid": "c",
            "username": "baz",
            "teamName": "",
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
        """ Create mock course metadata for serialization """
        course_org = "Oxford"
        course_name = "Introduction to Time Travel"
        course_number = "TT101"
        course_run = "2054"

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


@ddt.ddt
class TestScoreFieldAndSerializer(TestCase):
    """ Tests for ScoreField and ScoreSerializer """

    def test_field_no_values(self):
        """ An empty dict passed to the field should return None """
        assert ScoreField().to_representation({}) is None

    @ddt.data('pointsEarned', 'pointsPossible')
    def test_field_missing(self, missing_field):
        """ One missing field should result in the field defaulting to 0 """
        value = {'pointsEarned': 30, 'pointsPossible': 50}
        del value[missing_field]

        expectedValue = dict(value)
        expectedValue[missing_field] = 0

        actualValue = ScoreField().to_representation(value)
        assert expectedValue == actualValue

    def test_field(self):
        """ Base serialization behavior for ScoreField """
        data = {
            'pointsEarned': 20,
            'pointsPossible': 40
        }
        representation = ScoreField().to_representation(data)
        assert representation == data

    def test_serializer_no_values(self):
        """ Passing the ScoreSerializer an empty dict should result in two zeroes for the field """
        data = ScoreSerializer({}).data
        assert data == {'pointsEarned': 0, 'pointsPossible': 0}

    def test_serialier(self):
        """ Base serialization behavior for ScoreSerializer """
        input = {'pointsEarned': 10, 'pointsPossible': 200}
        data = ScoreSerializer(input).data
        assert data == input

    @ddt.data('pointsEarned', 'pointsPossible')
    def test_serializer_missing_field(self, missing_field):
        """ One missing field should result in the field defaulting to 0 """
        value = {'pointsEarned': 30, 'pointsPossible': 50}
        del value[missing_field]

        expectedValue = dict(value)
        expectedValue[missing_field] = 0

        actualValue = ScoreSerializer(value).data
        assert expectedValue == actualValue


class TestUploadedFileSerializer(TestCase):
    """ Tests for UploadedFileSerializer """

    def test_uploaded_file_serializer(self):
        """ Base serialization behavior """
        input = MagicMock()
        data = UploadedFileSerializer(input).data

        expected_value = {
            'downloadURL': str(input.download_url),
            'description': str(input.description),
            'name': str(input.name),
        }
        assert data == expected_value


@ddt.ddt
class TestResponseSerializer(TestCase):
    """ Tests for ResponseSerializer """

    def test_response_serializer__empty(self):
        """ Empty fields should be allowed """
        input = {'files': [], 'text': []}
        assert ResponseSerializer(input).data == input

    @ddt.unpack
    @ddt.data((True, True), (True, False), (False, True), (False, False))
    def test_response_serializer(self, has_text, has_files):
        """ Base serialization behavior """
        input = MagicMock()
        if has_files:
            input.files = [Mock(), Mock(), Mock()]
        if has_text:
            input.text = [Mock(), Mock(), Mock()]

        data = ResponseSerializer(input).data
        expected_value = {
            'files': [UploadedFileSerializer(mock_file).data for mock_file in input.files] if has_files else [],
            'text': [str(mock_text) for mock_text in input.text] if has_text else [],
        }
        assert data == expected_value


class TestAssessmentCriteriaSerializer(TestCase):
    """ Tests for AssessmentCriteriaSerializer """

    def test_assessment_criteria_serializer(self):
        """ Base serialization behavior """
        input = Mock()
        data = AssessmentCriteriaSerializer(input).data

        expected_value = {
            'name': str(input.name),
            'feedback': str(input.feedback),
            'selectedOption': str(input.option),
        }
        assert data == expected_value

    def test_assessment_criteria_serializer__feedback_only(self):
        """ Test for serialization behavior of a feedback-only criterion """
        input = {
            'name': 'SomeCriterioOn',
            'feedback': 'Pathetic Effort',
            'option': None,
        }
        data = AssessmentCriteriaSerializer(input).data

        expected_value = dict(input)
        expected_value['selectedOption'] = expected_value['option']
        del expected_value['option']

        assert data == expected_value


@ddt.ddt
class TestGradeDataSerializer(TestCase):
    """ Tests for GradeDataSerializer """

    def test_grade_data_serializer__no_assessment(self):
        """ Passing an empty dict should result in an empty dict """
        assert GradeDataSerializer({}).data == {}

    @ddt.data(True, False)
    def test_grade_data_serializer__assessment(self, has_criteria):
        """ Base serialization behavior, with and without criteria """
        input = MagicMock()
        if has_criteria:
            input.criteria = [Mock(), Mock(), Mock()]
        data = GradeDataSerializer(input).data

        expected_value = {
            'score': ScoreField().to_representation(input.score),
            'overallFeedback': str(input.feedback)
        }
        if has_criteria:
            expected_value['criteria'] = [AssessmentCriteriaSerializer(criterion).data for criterion in input.criteria]
        else:
            expected_value['criteria'] = []
        assert data == expected_value


class TestSubmissionDetailResponseSerializer(TestCase):
    """ Tests for SubmissionDetailResponseSerializer """

    def test_submission_detail_response_serializer(self):
        """ Base serialization behavior """
        input = MagicMock()
        data = SubmissionDetailResponseSerializer(input).data

        expected_value = {
            'gradeData': GradeDataSerializer(input.assessment).data,
            'response': ResponseSerializer(input.submission).data
        }
        assert data == expected_value
