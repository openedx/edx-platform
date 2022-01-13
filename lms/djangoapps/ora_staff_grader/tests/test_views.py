"""
Tests for ESG views
"""
import ddt
import json

from uuid import uuid4
from django.http import QueryDict
from django.urls import reverse
from rest_framework.test import APITestCase
from unittest.mock import Mock, patch

from common.djangoapps.student.tests.factories import StaffFactory
from lms.djangoapps.ora_staff_grader.constants import (
    ERR_BAD_ORA_LOCATION,
    ERR_GRADE_CONTESTED,
    ERR_LOCK_CONTESTED,
    ERR_MISSING_PARAM,
    ERR_UNKNOWN,
    PARAM_ORA_LOCATION,
    PARAM_SUBMISSION_ID,
)
from lms.djangoapps.ora_staff_grader.errors import LockContestedError
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.factories import ItemFactory


class BaseViewTest(SharedModuleStoreTestCase, APITestCase):
    """ Base class for shared test utils and setup """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.api_url = reverse(cls.view_name)

        cls.course = CourseFactory.create()
        cls.course_key = cls.course.location.course_key

        cls.ora_block = ItemFactory.create(
            category='openassessment',
            parent_location=cls.course.location,
            display_name='test',
        )
        cls.ora_usage_key = str(cls.ora_block.location)

        cls.password = 'password'
        cls.staff = StaffFactory(course_key=cls.course_key, password=cls.password)

    def log_in(self):
        """ Log in as staff """
        self.client.login(username=self.staff.username, password=self.password)

    def url_with_params(self, params):
        """ For DRF client.posts, you can't add query params easily. This helper adds it to the request URL """
        query_dictionary = QueryDict('', mutable=True)
        query_dictionary.update(params)

        return '{base_url}?{querystring}'.format(
            base_url=reverse(self.view_name),
            querystring=query_dictionary.urlencode()
        )


@ddt.ddt
class TestInitializeView(BaseViewTest):
    """
    Tests for the /initialize view, creating setup data for ESG
    """
    view_name = 'ora-staff-grader:initialize'

    # Options split for reuse
    example_options = [
        {
            "order_num": 0,
            "name": "troll",
            "label": "Troll",
            "explanation": "Failing grade",
            "points": 0
        },
        {
            "order_num": 1,
            "name": "dreadful",
            "label": "Dreadful",
            "explanation": "Failing grade",
            "points": 1
        },
        {
            "order_num": 2,
            "name": "poor",
            "label": "Poor",
            "explanation": "Failing grade (may repeat)",
            "points": 2
        },
        {
            "order_num": 3,
            "name": "poor",
            "label": "Poor",
            "explanation": "Failing grade (may repeat)",
            "points": 3
        },
        {
            "order_num": 4,
            "name": "acceptable",
            "label": "Acceptable",
            "explanation": "Passing grade (may continue to N.E.W.T)",
            "points": 4
        },
        {
            "order_num": 5,
            "name": "exceeds_expectations",
            "label": "Exceeds Expectations",
            "explanation": "Passing grade (may continue to N.E.W.T)",
            "points": 5
        },
        {
            "order_num": 6,
            "name": "outstanding",
            "label": "Outstanding",
            "explanation": "Passing grade (will continue to N.E.W.T)",
            "points": 6
        }
    ]

    test_rubric = {
        "feedback_prompt": "How did this student do?",
        "feedback_default_text": "For the O.W.L exams, this student...",
        "criteria": [
            {
                "order_num": 0,
                "name": "potions",
                "label": "Potions",
                "prompt": "How did this student perform in the Potions exam",
                "feedback": "optional",
                "options": example_options
            },
            {
                "order_num": 1,
                "name": "charms",
                "label": "Charms",
                "prompt": "How did this student perform in the Charms exam",
                "feedback": "required",
                "options": example_options
            }
        ]
    }

    @ddt.data({}, {PARAM_ORA_LOCATION: ''})
    def test_missing_param(self, query_params):
        """ Missing ORA location param should return 400 and error message """
        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, query_params)

        assert response.status_code == 400
        assert json.loads(response.content) == {"error": ERR_MISSING_PARAM}

    def test_bad_ora_location(self):
        """ Bad ORA location should return a 400 and error message """
        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: 'not_a_real_location'})

        assert response.status_code == 400
        assert json.loads(response.content) == {"error": ERR_BAD_ORA_LOCATION}

    @patch('lms.djangoapps.ora_staff_grader.views.get_rubric_config')
    @patch('lms.djangoapps.ora_staff_grader.views.get_submissions')
    @patch('lms.djangoapps.ora_staff_grader.views.get_course_overview_or_none')
    def test_init(self, mock_get_course_overview, mock_get_submissions, mock_get_rubric_config):
        """ Any failure to fetch info returns an unknown error response """
        mock_course_overview = CourseOverviewFactory.create()
        mock_get_course_overview.return_value = mock_course_overview
        mock_get_submissions.return_value = {
            "a": {
                "submissionUuid": "a",
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
            }
        }
        mock_get_rubric_config.return_value = self.test_rubric

        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: self.ora_usage_key})

        expected_keys = set(['courseMetadata', 'oraMetadata', 'submissions', 'rubricConfig'])
        assert response.status_code == 200
        assert response.data.keys() == expected_keys

    @patch('lms.djangoapps.ora_staff_grader.views.get_rubric_config')
    @patch('lms.djangoapps.ora_staff_grader.views.get_submissions')
    @patch('lms.djangoapps.ora_staff_grader.views.get_course_overview_or_none')
    def test_init_exception(self, mock_get_course_overview, mock_get_submissions, mock_get_rubric_config):
        """ If one of the XBlock handlers fails, the exception should be caught """
        mock_course_overview = CourseOverviewFactory.create()
        mock_get_course_overview.return_value = mock_course_overview
        # Mock an error getting submissions
        mock_get_submissions.side_effect = Exception()
        mock_get_rubric_config.return_value = self.test_rubric

        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: self.ora_usage_key})

        assert response.status_code == 500
        assert json.loads(response.content) == {"error": ERR_UNKNOWN}


@ddt.ddt
class TestFetchSubmissionView(BaseViewTest):
    """
    Tests for the submission fetch view
    """
    view_name = 'ora-staff-grader:fetch-submission'

    @ddt.data({}, {PARAM_ORA_LOCATION: '', PARAM_SUBMISSION_ID: ''})
    def test_missing_params(self, query_params):
        """ Missing or blank params should return 400 and error message """
        self.log_in()
        response = self.client.get(self.api_url, query_params)

        assert response.status_code == 400
        assert json.loads(response.content) == {"error": ERR_MISSING_PARAM}

    @ddt.data(True, False)
    @patch('lms.djangoapps.ora_staff_grader.views.get_submission_info')
    @patch('lms.djangoapps.ora_staff_grader.views.get_assessment_info')
    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    def test_fetch_submission(
        self,
        has_assessment,
        mock_check_submission_lock,
        mock_get_assessment_info,
        mock_get_submission_info,
    ):
        """ Successfull submission fetch status returns submission, lock, and grade data """
        mock_submission = {
            'text': ['This is the answer'],
            'files': [
                {
                    'name': 'name_0',
                    'description': 'description_0',
                    'download_url': 'www.file_url.com/key_0',
                    'size': 123455,
                }
            ]
        }

        mock_assessment = {} if not has_assessment else {
            'feedback': "Base Assessment Feedback",
            'score': {
                'pointsEarned': 5,
                'pointsPossible': 6,
            },
            'criteria': [
                {
                    'name': "Criterion 1",
                    'option': "Three",
                    'points': 3,
                    'feedback': "Feedback 1"
                },
            ]
        }

        mock_get_submission_info.return_value = mock_submission
        mock_get_assessment_info.return_value = mock_assessment
        mock_check_submission_lock.return_value = {'lock_status': 'unlocked'}

        self.log_in()
        ora_location, submission_uuid = Mock(), Mock()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: ora_location, PARAM_SUBMISSION_ID: submission_uuid})

        assert response.status_code == 200
        assert response.data.keys() == set(['gradeData', 'response', 'gradeStatus', 'lockStatus'])
        assert response.data['response'].keys() == set(['files', 'text'])
        expected_assessment_keys = set(['score', 'overallFeedback', 'criteria']) if has_assessment else set()
        assert response.data['gradeData'].keys() == expected_assessment_keys

    @ddt.data(0, 1, 2)
    @patch('lms.djangoapps.ora_staff_grader.views.get_submission_info')
    @patch('lms.djangoapps.ora_staff_grader.views.get_assessment_info')
    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    def test_fetch_submission_exceptions(
        self,
        inject_chaos,
        mock_check_submission_lock,
        mock_get_assessment_info,
        mock_get_submission_info,
    ):
        """ An exception in any XBlock handler returns an error response """
        mock_submission = {
            'text': ['This is the answer'],
            'files': [
                {
                    'name': 'name_0',
                    'description': 'description_0',
                    'download_url': 'www.file_url.com/key_0',
                    'size': 123455,
                }
            ]
        }
        mock_assessment = {}

        mock_get_submission_info.return_value = mock_submission
        mock_get_assessment_info.return_value = mock_assessment
        mock_check_submission_lock.return_value = {'lock_status': 'unlocked'}

        mock_handlers = [mock_get_submission_info, mock_get_assessment_info, mock_check_submission_lock]
        mock_handlers[inject_chaos].side_effect = Exception()

        self.log_in()
        ora_location, submission_uuid = Mock(), Mock()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: ora_location, PARAM_SUBMISSION_ID: submission_uuid})

        assert response.status_code == 500
        assert json.loads(response.content) == {"error": ERR_UNKNOWN}


@ddt.ddt
class TestFetchSubmissionStatusView(BaseViewTest):
    """
    Tests for the submission fetch view
    """
    view_name = 'ora-staff-grader:fetch-submission-status'

    @ddt.data({}, {PARAM_ORA_LOCATION: '', PARAM_SUBMISSION_ID: Mock()}, {PARAM_ORA_LOCATION: Mock(), PARAM_SUBMISSION_ID: ''})
    def test_missing_param(self, query_params):
        """ Missing ORA location or submission ID param should return 400 and error message """
        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, query_params)

        assert response.status_code == 400
        assert json.loads(response.content) == {"error": ERR_MISSING_PARAM}

    @ddt.data(True, False)
    @patch('lms.djangoapps.ora_staff_grader.views.get_assessment_info')
    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    def test_fetch_submission_status(
        self,
        has_assessment,
        mock_check_submission_lock,
        mock_get_assessment_info,
    ):

        mock_assessment = {} if not has_assessment else {
            'feedback': "Base Assessment Feedback",
            'score': {
                'pointsEarned': 5,
                'pointsPossible': 6,
            },
            'criteria': [
                {
                    'name': "Criterion 1",
                    'option': "Three",
                    'points': 3,
                    'feedback': "Feedback 1"
                },
            ]
        }
        mock_get_assessment_info.return_value = mock_assessment

        mock_check_submission_lock.return_value = {'lock_status': 'in-progress'}

        self.log_in()
        ora_location, submission_uuid = Mock(), Mock()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: ora_location, PARAM_SUBMISSION_ID: submission_uuid})

        assert response.status_code == 200
        actual = response.json()
        expected = {
            'gradeStatus': 'graded' if has_assessment else 'ungraded',
            'lockStatus': mock_check_submission_lock.return_value['lock_status'],
            'gradeData': {} if not has_assessment else {
                'score': mock_assessment['score'],
                'overallFeedback': mock_assessment['feedback'],
                'criteria': [
                    {
                        'name': "Criterion 1",
                        'selectedOption': "Three",
                        'points': 3,
                        'feedback': "Feedback 1"
                    },
                ]
            }
        }
        assert actual == expected

    @patch('lms.djangoapps.ora_staff_grader.views.get_assessment_info')
    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    def test_fetch_submission_status_exceptions(self, mock_check_submission_lock, mock_get_assessment_info):
        """ Exceptions in any of the endpoints return a generic error response"""
        mock_get_assessment_info.side_effect = Exception()
        mock_check_submission_lock.side_effect = Exception()

        self.log_in()
        ora_location, submission_uuid = Mock(), Mock()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: ora_location, PARAM_SUBMISSION_ID: submission_uuid})

        assert response.status_code == 500
        assert json.loads(response.content) == {"error": ERR_UNKNOWN}


class TestSubmissionLockView(BaseViewTest):
    """
    Tests for the /lock view, locking or unlocking a submission for grading
    """
    view_name = 'ora-staff-grader:lock'

    test_submission_uuid = str(uuid4())
    test_anon_user_id = 'anon-user-id'
    test_other_anon_user_id = 'anon-user-id-2'
    test_timestamp = '2020-08-29T02:14:00-04:00'

    def setUp(self):
        super().setUp()

        # Lock requests must include ORA location and submission UUID
        self.test_lock_params = {
            PARAM_ORA_LOCATION: self.ora_usage_key,
            PARAM_SUBMISSION_ID: self.test_submission_uuid
        }

        self.client.login(username=self.staff.username, password=self.password)

    def claim_lock(self, params):
        """ Wrapper for easier calling of 'claim_submission_lock' """
        return self.client.post(self.url_with_params(params))

    def delete_lock(self, params):
        """ Wrapper for easier calling of 'delete_submission_lock' """
        return self.client.delete(self.url_with_params(params))

    # Tests for claiming a lock (POST)

    def test_claim_lock_invalid_ora(self):
        """ An invalid ORA returns a 400 """
        self.test_lock_params[PARAM_ORA_LOCATION] = 'not_a_real_location'

        response = self.claim_lock(self.test_lock_params)

        assert response.status_code == 400
        assert json.loads(response.content) == {"error": ERR_BAD_ORA_LOCATION}

    @patch('lms.djangoapps.ora_staff_grader.views.claim_submission_lock')
    def test_claim_lock(self, mock_claim_lock):
        """ POST tries to claim a submission lock. Success returns lock status 'in-progress'. """
        mock_return_data = {
            "submission_uuid": self.test_submission_uuid,
            "owner_id": self.test_anon_user_id,
            "created_at": self.test_timestamp,
            "lock_status": "in-progress"
        }
        mock_claim_lock.return_value = mock_return_data

        response = self.claim_lock(self.test_lock_params)

        expected_value = {"lockStatus": "in-progress"}
        assert response.status_code == 200
        assert json.loads(response.content) == expected_value

    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    @patch('lms.djangoapps.ora_staff_grader.views.claim_submission_lock')
    def test_claim_lock_contested(self, mock_claim_lock, mock_check_lock):
        """ Attempting to claim a lock owned by another user returns a 403 - forbidden and passes error code. """
        mock_claim_lock.side_effect = LockContestedError()
        mock_check_lock.return_value = {
            "submission_uuid": self.test_submission_uuid,
            "owner_id": self.test_other_anon_user_id,
            "created_at": self.test_timestamp,
            "lock_status": "locked"
        }

        response = self.claim_lock(self.test_lock_params)

        expected_value = {"error": ERR_LOCK_CONTESTED, "lockStatus": "locked"}
        assert response.status_code == 409
        assert json.loads(response.content) == expected_value

    # Tests for deleting a lock (DELETE)

    @patch('lms.djangoapps.ora_staff_grader.views.delete_submission_lock')
    def test_delete_lock(self, mock_delete_lock):
        """ DELETE indicates to clear submission lock. Success returns lock status 'unlocked'. """
        mock_delete_lock.return_value = {"lock_status": "unlocked"}

        response = self.delete_lock(self.test_lock_params)

        expected_value = {"lockStatus": "unlocked"}
        assert response.status_code == 200
        assert json.loads(response.content) == expected_value

    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    @patch('lms.djangoapps.ora_staff_grader.views.delete_submission_lock')
    def test_delete_lock_contested(self, mock_delete_lock, mock_check_lock):
        """ Attempting to delete a lock owned by another user returns a 403 - forbidden and passes error code. """
        mock_delete_lock.side_effect = LockContestedError()
        mock_check_lock.return_value = {
            "submission_uuid": self.test_submission_uuid,
            "owner_id": self.test_other_anon_user_id,
            "created_at": self.test_timestamp,
            "lock_status": "locked"
        }

        response = self.delete_lock(self.test_lock_params)

        expected_value = {"error": ERR_LOCK_CONTESTED, "lockStatus": "locked"}
        assert response.status_code == 409
        assert json.loads(response.content) == expected_value


class TestUpdateGradeView(BaseViewTest):
    """
    Tests for updating a grade for a submission
    """
    view_name = 'ora-staff-grader:update-grade'

    submission_uuid = str(uuid4())
    ora_location = Mock()
    test_anon_user_id = 'anon-user-id'
    test_timestamp = '2020-08-29T02:14:00-04:00'

    test_grade_data = {
        "overallFeedback": "was pretty good",
        "criteria": [
            {
                "name": "Ideas",
                "feedback": "did alright",
                "selectedOption": "Fair"
            },
            {
                "name": "Content",
                "selectedOption": "Excellent"
            }
        ]
    }

    def setUp(self):
        super().setUp()
        self.client.login(username=self.staff.username, password=self.password)

    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    @patch('lms.djangoapps.ora_staff_grader.views.submit_grade')
    def test_submit_grade_failure_handled(self, mock_submit_grade, mock_check_lock):
        """ A handled ORA failure to submit a grade returns a server error """
        mock_check_lock.return_value = {'lock_status': 'in-progress'}
        mock_submit_grade.return_value = {'success': False, 'msg': 'Danger, Will Robinson!'}
        url = self.url_with_params({PARAM_ORA_LOCATION: self.ora_location, PARAM_SUBMISSION_ID: self.submission_uuid})
        data = self.test_grade_data

        response = self.client.post(url, data, format='json')
        assert response.status_code == 500
        assert json.loads(response.content) == {
            "error": ERR_UNKNOWN
        }

    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    @patch('lms.djangoapps.ora_staff_grader.views.submit_grade')
    def test_submit_grade_failure_unhandled(self, mock_submit_grade, mock_check_lock):
        """ An exception anywhere submitting a grade returns a server error """
        mock_check_lock.return_value = {'lock_status': 'in-progress'}
        mock_submit_grade.side_effect = Exception()
        url = self.url_with_params({PARAM_ORA_LOCATION: self.ora_location, PARAM_SUBMISSION_ID: self.submission_uuid})
        data = self.test_grade_data

        response = self.client.post(url, data, format='json')
        assert response.status_code == 500
        assert json.loads(response.content) == {
            "error": ERR_UNKNOWN
        }

    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    @patch('lms.djangoapps.ora_staff_grader.views.get_assessment_info')
    @patch('lms.djangoapps.ora_staff_grader.views.delete_submission_lock')
    @patch('lms.djangoapps.ora_staff_grader.views.submit_grade')
    def test_submit_grade_success(self, mock_submit_grade, mock_delete_lock, mock_get_info, mock_check_lock):
        """ A grade update success should clear the submission lock and return submission meta """
        mock_check_lock.side_effect = [
            {'lock_status': 'in-progress'},
            {'lock_status': 'unlocked'}
        ]
        mock_submit_grade.return_value = {'success': True, 'msg': ''}
        mock_assessment = {
            'feedback': "Base Assessment Feedback",
            'score': {
                'pointsEarned': 5,
                'pointsPossible': 6,
            },
            'criteria': [
                {
                    'name': "Criterion 1",
                    'option': "Three",
                    'points': 3,
                    'feedback': "Feedback 1"
                },
            ]
        }
        mock_get_info.return_value = mock_assessment

        url = self.url_with_params({PARAM_ORA_LOCATION: self.ora_location, PARAM_SUBMISSION_ID: self.submission_uuid})
        data = self.test_grade_data

        response = self.client.post(url, data, format='json')

        expected_response = {
            'gradeStatus': 'graded',
            'lockStatus': 'unlocked',
            'gradeData': {
                'score': mock_assessment['score'],
                'overallFeedback': mock_assessment['feedback'],
                'criteria': [
                    {
                        'name': "Criterion 1",
                        'selectedOption': "Three",
                        'points': 3,
                        'feedback': "Feedback 1"
                    },
                ]
            }
        }

        assert response.status_code == 200
        assert json.loads(response.content) == expected_response

        # Verify that clear lock was called
        mock_delete_lock.assert_called_once()

    @patch('lms.djangoapps.ora_staff_grader.views.check_submission_lock')
    @patch('lms.djangoapps.ora_staff_grader.views.get_assessment_info')
    @patch('lms.djangoapps.ora_staff_grader.views.submit_grade')
    def test_submit_grade_contested(self, mock_submit_grade, mock_get_info, mock_check_lock):
        """ Submitting a grade should be blocked if someone else has obtained the lock """
        mock_check_lock.side_effect = [{'lock_status': 'unlocked'}]
        mock_assessment = {
            'feedback': "Base Assessment Feedback",
            'score': {
                'pointsEarned': 5,
                'pointsPossible': 6,
            },
            'criteria': [
                {
                    'name': "Criterion 1",
                    'option': "Three",
                    'points': 3,
                    'feedback': "Feedback 1"
                },
            ]
        }
        mock_get_info.return_value = mock_assessment

        url = self.url_with_params({PARAM_ORA_LOCATION: self.ora_location, PARAM_SUBMISSION_ID: self.submission_uuid})
        data = self.test_grade_data

        response = self.client.post(url, data, format='json')

        assert response.status_code == 409
        assert json.loads(response.content) == {
            "error": ERR_GRADE_CONTESTED,
            'gradeStatus': 'graded',
            'lockStatus': 'unlocked',
            'gradeData': {
                'score': mock_assessment['score'],
                'overallFeedback': mock_assessment['feedback'],
                'criteria': [
                    {
                        'name': "Criterion 1",
                        'selectedOption': "Three",
                        'points': 3,
                        'feedback': "Feedback 1"
                    },
                ]
            }
        }

        # Verify that submit grade was not called
        mock_submit_grade.assert_not_called()
