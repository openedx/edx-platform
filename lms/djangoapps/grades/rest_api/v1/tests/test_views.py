"""
Tests for v1 views
"""

from collections import OrderedDict
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import ddt
from django.db import connections
from django.urls import reverse
from opaque_keys import InvalidKeyError
from rest_framework import status
from rest_framework.test import APITestCase

from common.djangoapps.student.tests.factories import GlobalStaffFactory, UserFactory
from lms.djangoapps.courseware.tests.test_submitting_problems import TestSubmittingProblems
from lms.djangoapps.grades.rest_api.v1.tests.mixins import GradeViewTestMixin
from lms.djangoapps.grades.rest_api.v1.views import CourseGradesView
from openedx.core.djangoapps.user_authn.tests.utils import AuthAndScopesTestMixin
from xmodule.modulestore.tests.factories import BlockFactory


@ddt.ddt
class SingleUserGradesTests(GradeViewTestMixin, AuthAndScopesTestMixin, APITestCase):
    """
    Tests for grades related to a course and specific user
        e.g. /api/grades/v1/courses/{course_id}/?username={username}
             /api/grades/v1/courses/?course_id={course_id}&username={username}
    """
    default_scopes = CourseGradesView.required_scopes

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.namespaced_url = 'grades_api:v1:course_grades'

    def get_url(self, username):
        """ This method is required by AuthAndScopesTestMixin. """
        base_url = reverse(
            self.namespaced_url,
            kwargs={
                'course_id': self.course_key,
            }
        )
        return f"{base_url}?username={username}"

    def assert_success_response_for_student(self, response):
        """ This method is required by AuthAndScopesTestMixin. """
        expected_data = [{
            'username': self.student.username,
            'email': '',
            'letter_grade': None,
            'percent': 0.0,
            'course_id': str(self.course_key),
            'passed': False
        }]
        assert response.data == expected_data

    def test_nonexistent_user(self):
        """
        Test that a request for a nonexistent username returns an error.
        """
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(self.get_url('IDoNotExist'))
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_self_get_grade_not_enrolled(self):
        """
        Test that a user receives an error if she requests
        her own grade in a course where she is not enrolled.
        """
        # a user not enrolled in the course cannot request her grade
        unenrolled_user = UserFactory(password=self.password)
        self.client.login(username=unenrolled_user.username, password=self.password)
        resp = self.client.get(self.get_url(unenrolled_user.username))
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert 'error_code' in resp.data
        assert resp.data['error_code'] == 'user_not_enrolled'

    def test_no_grade(self):
        """
        Test the grade for a user who has not answered any test.
        """
        self.client.login(username=self.student.username, password=self.password)
        resp = self.client.get(self.get_url(self.student.username))
        assert resp.status_code == status.HTTP_200_OK
        expected_data = [{
            'username': self.student.username,
            'email': '',
            'course_id': str(self.course_key),
            'passed': False,
            'percent': 0.0,
            'letter_grade': None
        }]

        assert resp.data == expected_data

    def test_wrong_course_key(self):
        """
        Test that a request for an invalid course key returns an error.
        """
        def mock_from_string(*args, **kwargs):
            """Mocked function to always raise an exception"""
            raise InvalidKeyError('foo', 'bar')

        self.client.login(username=self.student.username, password=self.password)
        with patch('opaque_keys.edx.keys.CourseKey.from_string', side_effect=mock_from_string):
            resp = self.client.get(self.get_url(self.student.username))

        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert 'error_code' in resp.data
        assert resp.data['error_code'] == 'invalid_course_key'

    def test_course_does_not_exist(self):
        """
        Test that requesting a valid, nonexistent course key returns an error as expected.
        """
        self.client.login(username=self.student.username, password=self.password)
        base_url = reverse(
            self.namespaced_url,
            kwargs={
                'course_id': 'course-v1:MITx+8.MechCX+2014_T1',
            }
        )
        url = f"{base_url}?username={self.student.username}"
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert 'error_code' in resp.data
        assert resp.data['error_code'] == 'course_does_not_exist'

    @ddt.data(
        ({'letter_grade': None, 'percent': 0.4, 'passed': False}),
        ({'letter_grade': 'Pass', 'percent': 1, 'passed': True}),
    )
    def test_grade(self, grade):
        """
        Test that the user gets her grade in case she answered tests with an insufficient score.
        """
        self.client.login(username=self.student.username, password=self.password)
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            grade_fields = {
                'letter_grade': grade['letter_grade'],
                'percent': grade['percent'],
                'passed': grade['letter_grade'] is not None,

            }
            mock_grade.return_value = MagicMock(**grade_fields)
            resp = self.client.get(self.get_url(self.student.username))

        assert resp.status_code == status.HTTP_200_OK
        expected_data = {
            'username': self.student.username,
            'email': '',
            'course_id': str(self.course_key),
        }

        expected_data.update(grade)
        assert resp.data == [expected_data]


@ddt.ddt
class CourseGradesViewTest(GradeViewTestMixin, APITestCase):
    """
    Tests for grades related to all users in a course
        e.g. /api/grades/v1/courses/{course_id}/
             /api/grades/v1/courses/?course_id={course_id}
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.namespaced_url = 'grades_api:v1:course_grades'

    def get_url(self, course_key=None):
        """
        Helper function to create the url
        """
        base_url = reverse(
            self.namespaced_url,
            kwargs={
                'course_id': course_key or self.course_key,
            }
        )

        return base_url

    def test_anonymous(self):
        resp = self.client.get(self.get_url())
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student(self):
        self.client.login(username=self.student.username, password=self.password)
        resp = self.client.get(self.get_url())
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_course_does_not_exist(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(course_key='course-v1:MITx+8.MechCX+2014_T1')
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_course_no_enrollments(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(course_key=self.empty_course.id)
        )
        assert resp.status_code == status.HTTP_200_OK
        expected_data = OrderedDict([
            ('next', None),
            ('previous', None),
            ('results', []),
        ])
        assert expected_data == resp.data

    def test_staff_can_get_all_grades(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(self.get_url())

        # this should have permission to access this API endpoint
        assert resp.status_code == status.HTTP_200_OK
        expected_data = OrderedDict([
            ('next', None),
            ('previous', None),
            ('results', [
                {
                    'username': self.student.username,
                    'email': '',
                    'course_id': str(self.course.id),
                    'passed': False,
                    'percent': 0.0,
                    'letter_grade': None
                },
                {
                    'username': self.other_student.username,
                    'email': '',
                    'course_id': str(self.course.id),
                    'passed': False,
                    'percent': 0.0,
                    'letter_grade': None
                },
                {
                    'username': self.program_student.username,
                    'email': '',
                    'course_id': str(self.course.id),
                    'passed': False,
                    'percent': 0.0,
                    'letter_grade': None,
                },
                {
                    'username': self.program_masters_student.username,
                    'email': self.program_masters_student.email,
                    'course_id': str(self.course.id),
                    'passed': False,
                    'percent': 0.0,
                    'letter_grade': None,
                },
            ]),
        ])

        assert expected_data == resp.data


class SectionGradesBreakdownTest(GradeViewTestMixin, APITestCase):
    """
    Tests for course grading status for all users in a course
        e.g. /api/grades/v1/section_grades_breakdown
            /api/grades/v1/section_grades_breakdown/?course_id={course_id}
           /api/grades/v1/section_grades_breakdown/?course_id={course_id}&username={username}
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.namespaced_url = 'grades_api:v1:section_grades_breakdown'
        cls.section_breakdown = (
            [
                {
                    'category': 'Homework',
                    'detail': f'Homework {i} Unreleased - 0% (?/?)',
                    'label': f'HW {i:02d}', 'percent': .0
                }
                for i in range(1, 11)
            ]
            + [
                {
                    'category': 'Homework',
                    'detail': 'Homework 11 Unreleased - 0% (?/?)',
                    'label': 'HW 11',
                    'mark': {'detail': 'The lowest 2 Homework scores are dropped.'},
                    'percent': 0.0
                },
                {
                    'category': 'Homework',
                    'detail': 'Homework 12 Unreleased - 0% (?/?)',
                    'label': 'HW 12',
                    'mark': {'detail': 'The lowest 2 Homework scores are dropped.'},
                    'percent': 0.0
                }
            ]
            + [
                {
                    'category': 'Homework',
                    'detail': 'Homework Average = 0.00%',
                    'label': 'HW Avg', 'percent': 0.0,
                    'prominent': True
                }
            ]
            + [
                {
                    'category': 'Lab',
                    'detail': f'Lab {i} Unreleased - 0% (?/?)',
                    'label': f'Lab {i:02d}', 'percent': .0
                }
                for i in range(1, 11)
            ]
            + [
                {
                    'category': 'Lab',
                    'detail': 'Lab 11 Unreleased - 0% (?/?)',
                    'label': 'Lab 11',
                    'mark': {'detail': 'The lowest 2 Lab scores are dropped.'},
                    'percent': 0.0
                },
                {
                    'category': 'Lab',
                    'detail': 'Lab 12 Unreleased - 0% (?/?)',
                    'label': 'Lab 12',
                    'mark': {'detail': 'The lowest 2 Lab scores are dropped.'},
                    'percent': 0.0
                },
                {
                    'category': 'Lab',
                    'detail': 'Lab Average = 0.00%',
                    'label': 'Lab Avg',
                    'percent': 0.0,
                    'prominent': True
                },
                {
                    'category': 'Midterm Exam',
                    'detail': 'Midterm Exam = 0.00%',
                    'label': 'Midterm',
                    'percent': 0.0,
                    'prominent': True
                },
                {
                    'category': 'Final Exam',
                    'detail': 'Final Exam = 0.00%',
                    'label': 'Final',
                    'percent': 0.0,
                    'prominent': True
                }
            ]
        )

    def get_url(self, query_params=None):
        """
        Helper function to create the url
        """
        base_url = reverse(
            self.namespaced_url,
        )
        if query_params:
            base_url = f'{base_url}?{query_params}'
        return base_url

    def test_anonymous(self):
        resp = self.client.get(self.get_url())
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student(self):
        self.client.login(username=self.student.username, password=self.password)
        resp = self.client.get(self.get_url())
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_course_does_not_exist(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(
                urlencode({'course_id': 'course-v1:MITx+8.MechCX+2014_T1'})
            )
        )
        expected_data = OrderedDict(
            [
                ('next', None),
                ('previous', None),
                ('results', [])
            ]
        )
        assert resp.status_code == status.HTTP_200_OK
        assert expected_data == resp.data

    def test_course_no_enrollments(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(urlencode({'course_id': self.empty_course.id}))
        )
        assert resp.status_code == status.HTTP_200_OK
        expected_data = OrderedDict(
            [
                ('next', None),
                ('previous', None),
                ('results', []),
            ]
        )
        assert expected_data == resp.data

    def test_staff_can_get_all_grades(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(self.get_url(urlencode({'course_id': self.course_key})))

        # This should have permission to access this API endpoint.
        assert resp.status_code == status.HTTP_200_OK
        expected_data = OrderedDict(
            [
                ('next', None),
                ('previous', None),
                (
                    'results',
                    [
                        {
                            'course_id': str(self.course_key),
                            'current_grade': 0,
                            'passed': False,
                            'section_breakdown': self.section_breakdown,
                            'username': 'student'
                        },
                        {
                            'course_id': str(self.course_key),
                            'current_grade': 0,
                            'passed': False,
                            'section_breakdown': self.section_breakdown,
                            'username': 'other_student'
                        },
                        {
                            'course_id': str(self.course_key),
                            'current_grade': 0,
                            'passed': False,
                            'section_breakdown': self.section_breakdown,
                            'username': 'program_student'
                        },
                        {
                            'course_id': str(self.course_key),
                            'current_grade': 0,
                            'passed': False,
                            'section_breakdown': self.section_breakdown,
                            'username': 'program_masters_student'
                        }
                    ]
                )
            ]
        )
        assert expected_data == resp.data

    def test_staff_can_get_all_grades_for_user(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(self.get_url(urlencode({'course_id': self.course_key,
                                                       'username': 'student'})))

        # this should have permission to access this API endpoint
        assert resp.status_code == status.HTTP_200_OK
        expected_data = OrderedDict(
            [
                ('next', None),
                ('previous', None),
                (
                    'results',
                    [
                        {
                            'course_id': str(self.course_key),
                            'current_grade': 0,
                            'passed': False,
                            'section_breakdown': self.section_breakdown,
                            'username': 'student'
                        }
                    ]
                )
            ]
        )
        assert expected_data == resp.data


class CourseSubmissionHistoryTest(GradeViewTestMixin, APITestCase):
    """
    Tests for course submission history for all users in a course
        e.g. /api/grades/v1/submission_history/{course_id}
            /api/grades/v1/submission_history/{course_id}/?username={username}
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.namespaced_url = 'grades_api:v1:submission_history'

    def get_url(self, course_key, query_params=None):
        """
        Helper function to create the url
        """
        base_url = reverse(
            self.namespaced_url,
            kwargs={
                'course_id': course_key,
            }
        )
        if query_params:
            base_url = f'{base_url}?{query_params}'
        return base_url

    def test_anonymous(self):
        resp = self.client.get(self.get_url(course_key=self.course_key))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student(self):
        self.client.login(username=self.student.username, password=self.password)
        resp = self.client.get(self.get_url(course_key=self.course_key))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_course_does_not_exist(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(course_key='course-v1:MITx+8.MechCX+2014_T1')
        )
        expected_data = OrderedDict([('next', None), ('previous', None), ('results', [])])
        assert resp.status_code == status.HTTP_200_OK
        assert expected_data == resp.data

    def test_course_no_enrollments(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(course_key=self.empty_course.id)
        )
        assert resp.status_code == status.HTTP_200_OK
        expected_data = OrderedDict([('next', None), ('previous', None), ('results', [])])
        assert expected_data == resp.data


class CourseSubmissionHistoryWithDataTest(TestSubmittingProblems):
    """
    Tests for course submission history for all users in a course
        e.g. /api/grades/v1/submission_history/?course_id={course_id}
            /api/grades/v1/submission_history?course_id={course_id}&username={username}
    """

    # Tell Django to clean out all databases, not just default
    databases = set(connections)

    def setUp(self):
        super().setUp()
        self.namespaced_url = 'grades_api:v1:submission_history'
        self.password = self.TEST_PASSWORD
        self.basic_setup()
        self.global_staff = GlobalStaffFactory.create()

    def basic_setup(self, late=False, reset=False, showanswer=False):
        """
        Set up a simple course for testing basic grading functionality.
        """
        grading_policy = {
            "GRADER": [{
                "type": "Homework",
                "min_count": 1,
                "drop_count": 0,
                "short_label": "HW",
                "weight": 1.0
            }],
            "GRADE_CUTOFFS": {
                'A': .9,
                'B': .33
            }
        }
        self.add_grading_policy(grading_policy)

        # set up a simple course with four problems
        homework = self.add_graded_section_to_course('homework', late=late, reset=reset, showanswer=showanswer)
        vertical = BlockFactory.create(
            parent_location=homework.location,
            category='vertical',
            display_name='Subsection 1',
        )
        self.add_dropdown_to_section(vertical.location, 'p1', 1)
        self.add_dropdown_to_section(vertical.location, 'p2', 1)
        self.add_dropdown_to_section(vertical.location, 'p3', 1)

        self.refresh_course()

    def get_url(self, course_key, query_params=None):
        """
        Helper function to create the url
        """
        base_url = reverse(
            self.namespaced_url,
            kwargs={
                'course_id': course_key,
            }
        )
        if query_params:
            base_url = f'{base_url}?{query_params}'
        return base_url

    def test_course_exist_with_data(self):
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(
                course_key=self.course.id,
            )
        )
        assert resp.status_code == status.HTTP_200_OK
        resp_json = resp.json()['results'][0]
        assert resp_json['course_id'] == str(self.course.id)
        assert resp_json['course_name'] == 'test_course'
        assert len(resp_json['problems']) > 0
        assert len(resp_json['problems'][0]['submission_history']) > 0
