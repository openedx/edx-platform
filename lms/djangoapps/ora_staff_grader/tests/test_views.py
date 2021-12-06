"""
Tests for ESG views
"""
import ddt
import json

from uuid import uuid4
from django.http import QueryDict
from django.http.response import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from rest_framework.test import APITestCase
from unittest.mock import Mock, patch

from common.djangoapps.student.tests.factories import StaffFactory
from lms.djangoapps.ora_staff_grader.errors import ERR_BAD_ORA_LOCATION, ERR_MISSING_PARAM
from lms.djangoapps.ora_staff_grader.views import PARAM_ORA_LOCATION, PARAM_SUBMISSION_ID
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


class TestInitializeView(BaseViewTest):
    """
    Tests for the /initialize view, creating setup data for ESG
    """
    view_name = 'ora-staff-grader:initialize'

    def test_missing_ora_location(self):
        """ Missing ORA location param should return 400 and error message """
        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url)

        assert response.status_code == 400
        assert response.content.decode() == ERR_MISSING_PARAM

    def test_bad_ora_location(self):
        """ Bad ORA location should return a 400 and error message """
        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: 'not_a_real_location'})

        assert response.status_code == 400
        assert response.content.decode() == ERR_BAD_ORA_LOCATION

    @patch('lms.djangoapps.ora_staff_grader.views.InitializeView.get_rubric_config')
    @patch('lms.djangoapps.ora_staff_grader.views.InitializeView.get_submissions')
    @patch('lms.djangoapps.ora_staff_grader.views.get_course_overview_or_none')
    def test_init(self, mock_get_course_overview, mock_get_submissions, mock_get_rubric_config):
        """ A successful call should return course, ORA, submissions, and rubric data """
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

        # Rubric data is passed through directly, so we can use a toy data payload
        mock_get_rubric_config.return_value = {"foo": "bar"}

        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: self.ora_usage_key})

        expected_keys = set(['courseMetadata', 'oraMetadata', 'submissions', 'rubricConfig'])
        assert response.status_code == 200
        assert response.data.keys() == expected_keys


@ddt.ddt
class TestFetchSubmissionView(BaseViewTest):
    """
    Tests for the submission fetch view
    """
    view_name = 'ora-staff-grader:fetch-submission'

    def test_missing_ora_location(self):
        """ Missing ora_location param should return 400 and error message """
        self.log_in()
        response = self.client.get(self.api_url)

        assert response.status_code == 400
        assert response.content.decode() == ERR_MISSING_PARAM

    def test_blank_ora_location(self):
        """ Blank ORA location should return 400 and error message """
        self.log_in()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: ''})

        assert response.status_code == 400
        assert response.content.decode() == ERR_MISSING_PARAM

    def test_missing_submission_uuid(self):
        """ Missing submission UUID should return 400 and error message """
        self.log_in()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: Mock()})

        assert response.status_code == 400
        assert response.content.decode() == ERR_MISSING_PARAM

    def test_blank_submission_uuid(self):
        """ Blank submission UUID should return 400 and error message """
        self.log_in()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: Mock(), PARAM_SUBMISSION_ID: ''})

        assert response.status_code == 400
        assert response.content.decode() == ERR_MISSING_PARAM

    @ddt.data(True, False)
    @patch('lms.djangoapps.ora_staff_grader.views.SubmissionFetchView.get_submission_info')
    @patch('lms.djangoapps.ora_staff_grader.views.SubmissionFetchView.get_assessment_info')
    @patch('lms.djangoapps.ora_staff_grader.views.SubmissionFetchView.check_submission_lock')
    def test_fetch_submission(
        self,
        has_assessment,
        mock_check_submission_lock,
        mock_get_assessment_info,
        mock_get_submission_info,
    ):
        """ """
        mock_submission = {
            'text': ['This is the answer'],
            'files': [
                {
                    'name': 'name_0',
                    'description': 'description_0',
                    'download_url': 'www.file_url.com/key_0'
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


@ddt.ddt
class TestFetchSubmissionStatusView(BaseViewTest):
    """
    Tests for the submission fetch view
    """
    view_name = 'ora-staff-grader:fetch-submission-status'

    def test_missing_ora_location(self):
        """ Missing ORA location should return 400 and error message """
        self.log_in()
        response = self.client.get(self.api_url)

        assert response.status_code == 400
        assert response.content.decode() == ERR_MISSING_PARAM

    def test_blank_ora_location(self):
        """ Empty ORA location should return 400 and error message """
        self.log_in()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: ''})

        assert response.status_code == 400
        assert response.content.decode() == ERR_MISSING_PARAM

    def test_missing_submission_uuid(self):
        """ Missing submission UUID should return 400 and error message """
        self.log_in()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: Mock()})

        assert response.status_code == 400
        assert response.content.decode() == ERR_MISSING_PARAM

    def test_blank_submission_uuid(self):
        """ Blank submission UUID should return 400 and error message """
        self.log_in()
        response = self.client.get(self.api_url, {PARAM_ORA_LOCATION: Mock(), PARAM_SUBMISSION_ID: ''})

        assert response.status_code == 400
        assert response.content.decode() == ERR_MISSING_PARAM

    @ddt.data(True, False)
    @patch('lms.djangoapps.ora_staff_grader.views.SubmissionStatusFetchView.get_assessment_info')
    @patch('lms.djangoapps.ora_staff_grader.views.SubmissionStatusFetchView.check_submission_lock')
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


class TestSubmissionLockView(APITestCase):
    """
    Tests for the /lock view, locking or unlocking a submission for grading
    """
    view_name = 'ora-staff-grader:lock'
    api_url = reverse(view_name)

    test_submission_uuid = str(uuid4())
    test_anon_user_id = 'anon-user-id'
    test_timestamp = '2020-08-29T02:14:00-04:00'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_key = CourseKey.from_string('course-v1:edX+ToyX+Toy_Course')
        cls.test_ora_location = 'block-v1:edX+ToyX+Toy_Course+type@openassessment+block@f00'
        cls.password = 'password'
        cls.staff = StaffFactory(course_key=cls.course_key, password=cls.password)

    def setUp(self):
        super().setUp()

        # Lock requests must include ORA location and submission UUID
        self.test_lock_params = {
            PARAM_ORA_LOCATION: self.test_ora_location,
            PARAM_SUBMISSION_ID: self.test_submission_uuid
        }

        self.client.login(username=self.staff.username, password=self.password)

    def _url_with_params(self, params):
        """ For DRF client.posts, you can't add query params easily. This helper adds it to the request URL """
        query_dictionary = QueryDict('', mutable=True)
        query_dictionary.update(params)

        return '{base_url}?{querystring}'.format(
            base_url=reverse(self.view_name),
            querystring=query_dictionary.urlencode()
        )

    def claim_lock(self, params):
        """ Wrapper for easier calling of 'claim_submission_lock' """
        return self.client.post(self._url_with_params(params))

    def delete_lock(self, params):
        """ Wrapper for easier calling of 'delete_submission_lock' """
        return self.client.delete(self._url_with_params(params))

    # Tests for claiming a lock (POST)

    def test_claim_lock_invalid_ora(self):
        """ An invalid ORA returns a 400 """
        self.test_lock_params[PARAM_ORA_LOCATION] = 'not_a_real_location'

        response = self.claim_lock(self.test_lock_params)

        assert response.status_code == 400
        assert response.content.decode() == ERR_BAD_ORA_LOCATION

    @patch('lms.djangoapps.ora_staff_grader.views.call_xblock_json_handler')
    def test_claim_lock(self, mock_xblock_handler):
        """ Passing value=True indicates to claim a submission lock. Success returns lock status 'in-progress'. """
        mock_return_data = {
            "submission_uuid": self.test_submission_uuid,
            "owner_id": self.test_anon_user_id,
            "created_at": self.test_timestamp,
            "lock_status": "in-progress"
        }
        mock_xblock_handler.return_value = HttpResponse(json.dumps(mock_return_data), content_type="application/json")

        response = self.claim_lock(self.test_lock_params)

        expected_value = {"lockStatus": "in-progress"}
        assert response.status_code == 200
        assert json.loads(response.content) == expected_value

    @patch('lms.djangoapps.ora_staff_grader.views.call_xblock_json_handler')
    def test_claim_lock_contested(self, mock_xblock_handler):
        """ Attempting to claim a lock owned by another user returns a 403 - forbidden and passes error code. """
        mock_return_data = {
            "error": "ERR_LOCK_CONTESTED"
        }
        mock_xblock_handler.return_value = HttpResponseForbidden(json.dumps(mock_return_data), content_type="application/json")

        response = self.claim_lock(self.test_lock_params)

        expected_value = mock_return_data
        assert response.status_code == 403
        assert json.loads(response.content) == expected_value

    # Tests for deleting a lock (DELETE)

    @patch('lms.djangoapps.ora_staff_grader.views.call_xblock_json_handler')
    def test_delete_lock(self, mock_xblock_handler):
        """ Passing value=False indicates to delete a submission lock. Success returns lock status 'unlocked'. """
        mock_return_data = {
            "submission_uuid": "",
            "owner_id": "",
            "created_at": "",
            "lock_status": "unlocked"
        }
        mock_xblock_handler.return_value = HttpResponse(json.dumps(mock_return_data), content_type="application/json")

        response = self.delete_lock(self.test_lock_params)

        expected_value = {"lockStatus": "unlocked"}
        assert response.status_code == 200
        assert json.loads(response.content) == expected_value

    @patch('lms.djangoapps.ora_staff_grader.views.call_xblock_json_handler')
    def test_delete_lock_contested(self, mock_xblock_handler):
        """ Attempting to delete a lock owned by another user returns a 403 - forbidden and passes error code. """
        mock_return_data = {
            "error": "ERR_LOCK_CONTESTED"
        }
        mock_xblock_handler.return_value = HttpResponseForbidden(json.dumps(mock_return_data), content_type="application/json")

        response = self.delete_lock(self.test_lock_params)

        expected_value = mock_return_data
        assert response.status_code == 403
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

    def _url_with_params(self, params):
        """ For DRF client.posts, you can't add query params easily. This helper adds it to the request URL """
        query_dictionary = QueryDict('', mutable=True)
        query_dictionary.update(params)

        return '{base_url}?{querystring}'.format(
            base_url=reverse(self.view_name),
            querystring=query_dictionary.urlencode()
        )

    def setUp(self):
        super().setUp()
        self.client.login(username=self.staff.username, password=self.password)

    @patch('lms.djangoapps.ora_staff_grader.views.UpdateGradeView.submit_grade')
    def test_submit_grade_failure(self, mock_submit_grade):
        """ An ORA failure to submit a grade returns a server error """
        mock_submit_grade.return_value = {'success': False, 'msg': 'Danger, Will Robinson!'}
        url = self._url_with_params({PARAM_ORA_LOCATION: self.ora_location, PARAM_SUBMISSION_ID: self.submission_uuid})
        data = self.test_grade_data

        response = self.client.post(url, data, format='json')
        assert response.status_code == 500
        assert response.content.decode() == mock_submit_grade.return_value['msg']

    @patch('lms.djangoapps.ora_staff_grader.views.UpdateGradeView.check_submission_lock')
    @patch('lms.djangoapps.ora_staff_grader.views.UpdateGradeView.get_assessment_info')
    @patch('lms.djangoapps.ora_staff_grader.views.UpdateGradeView.delete_submission_lock')
    @patch('lms.djangoapps.ora_staff_grader.views.UpdateGradeView.submit_grade')
    def test_submit_grade_success(self, mock_submit_grade, mock_delete_lock, mock_get_info, mock_check_lock):
        """ A grade update success should clear the submission lock and return submission meta """
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
        mock_check_lock.return_value = {'lock_status': 'unlocked'}

        url = self._url_with_params({PARAM_ORA_LOCATION: self.ora_location, PARAM_SUBMISSION_ID: self.submission_uuid})
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

    def test_submit_lock_contested(self):
        """ TODO - Submitting a grade should be blocked if someone else has obtained the lock """
        pass

    def test_parital_success(self):
        """ TODO - For success in updating a grade but failure to clear lock or get submission meta... ? """
        pass
