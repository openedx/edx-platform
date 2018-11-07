"""
Tests for v1 views
"""
from datetime import datetime
import ddt

from django.urls import reverse
from mock import MagicMock, patch
from opaque_keys import InvalidKeyError
from pytz import UTC
from rest_framework import status
from rest_framework.test import APITestCase

from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory, StaffFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE


class GradeViewTestMixin(SharedModuleStoreTestCase):
    """
    Mixin class for grades related view tests
    The following tests assume that the grading policy is the edX default one:
    {
        "GRADER": [
            {
                "drop_count": 2,
                "min_count": 12,
                "short_label": "HW",
                "type": "Homework",
                "weight": 0.15
            },
            {
                "drop_count": 2,
                "min_count": 12,
                "type": "Lab",
                "weight": 0.15
            },
            {
                "drop_count": 0,
                "min_count": 1,
                "short_label": "Midterm",
                "type": "Midterm Exam",
                "weight": 0.3
            },
            {
                "drop_count": 0,
                "min_count": 1,
                "short_label": "Final",
                "type": "Final Exam",
                "weight": 0.4
            }
        ],
        "GRADE_CUTOFFS": {
            "Pass": 0.5
        }
    }
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(GradeViewTestMixin, cls).setUpClass()

        cls.course = cls._create_test_course_with_default_grading_policy(
            display_name='test course', run="Testing_course"
        )
        cls.empty_course = cls._create_test_course_with_default_grading_policy(
            display_name='empty test course', run="Empty_testing_course"
        )

        cls.course_key = cls.course.id

        cls.password = 'test'
        cls.student = UserFactory(username='dummy', password=cls.password)
        cls.other_student = UserFactory(username='foo', password=cls.password)
        cls.other_user = UserFactory(username='bar', password=cls.password)
        cls.staff = StaffFactory(course_key=cls.course_key, password=cls.password)
        cls.global_staff = GlobalStaffFactory.create()
        date = datetime(2013, 1, 22, tzinfo=UTC)
        for user in (cls.student, cls.other_student,):
            CourseEnrollmentFactory(
                course_id=cls.course.id,
                user=user,
                created=date,
            )

    def setUp(self):
        super(GradeViewTestMixin, self).setUp()
        self.client.login(username=self.student.username, password=self.password)

    @classmethod
    def _create_test_course_with_default_grading_policy(cls, display_name, run):
        """
        Utility method to create a course with a default grading policy
        """
        course = CourseFactory.create(display_name=display_name, run=run)
        _ = CourseOverviewFactory.create(id=course.id)

        chapter = ItemFactory.create(
            category='chapter',
            parent_location=course.location,
            display_name="Chapter 1",
        )
        # create a problem for each type and minimum count needed by the grading policy
        # A section is not considered if the student answers less than "min_count" problems
        for grading_type, min_count in (("Homework", 12), ("Lab", 12), ("Midterm Exam", 1), ("Final Exam", 1)):
            for num in xrange(min_count):
                section = ItemFactory.create(
                    category='sequential',
                    parent_location=chapter.location,
                    due=datetime(2017, 12, 18, 11, 30, 00),
                    display_name='Sequential {} {}'.format(grading_type, num),
                    format=grading_type,
                    graded=True,
                )
                vertical = ItemFactory.create(
                    category='vertical',
                    parent_location=section.location,
                    display_name='Vertical {} {}'.format(grading_type, num),
                )
                ItemFactory.create(
                    category='problem',
                    parent_location=vertical.location,
                    display_name='Problem {} {}'.format(grading_type, num),
                )

        return course


@ddt.ddt
class SingleUserGradesTests(GradeViewTestMixin, APITestCase):
    """
    Tests for grades related to a course and specific user
        e.g. /api/grades/v1/courses/{course_id}/?username={username}
             /api/grades/v1/courses/?course_id={course_id}&username={username}
    """

    @classmethod
    def setUpClass(cls):
        super(SingleUserGradesTests, cls).setUpClass()
        cls.namespaced_url = 'grades_api:v1:course_grades'

    def get_url(self, username):
        """
        Helper function to create the url
        """
        base_url = reverse(
            self.namespaced_url,
            kwargs={
                'course_id': self.course_key,
            }
        )
        return "{0}?username={1}".format(base_url, username)

    def test_anonymous(self):
        """
        Test that an anonymous user cannot access the API and an error is received.
        """
        self.client.logout()
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_self_get_grade(self):
        """
        Test that a user can successfully request her own grade.
        """
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_nonexistent_user(self):
        """
        Test that a request for a nonexistent username returns an error.
        """
        self.client.logout()
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(self.get_url('IDoNotExist'))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_other_get_grade(self):
        """
        Test that if a user requests the grade for another user, she receives an error.
        """
        self.client.logout()
        self.client.login(username=self.other_student.username, password=self.password)
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_self_get_grade_not_enrolled(self):
        """
        Test that a user receives an error if she requests
        her own grade in a course where she is not enrolled.
        """
        # a user not enrolled in the course cannot request her grade
        self.client.logout()
        self.client.login(username=self.other_user.username, password=self.password)
        resp = self.client.get(self.get_url(self.other_user.username))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error_code', resp.data)
        self.assertEqual(
            resp.data['error_code'],
            'user_not_enrolled'
        )

    def test_no_grade(self):
        """
        Test the grade for a user who has not answered any test.
        """
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = [{
            'username': self.student.username,
            'email': self.student.email,
            'course_id': str(self.course_key),
            'passed': False,
            'percent': 0.0,
            'letter_grade': None
        }]

        self.assertEqual(resp.data, expected_data)

    def test_wrong_course_key(self):
        """
        Test that a request for an invalid course key returns an error.
        """
        def mock_from_string(*args, **kwargs):  # pylint: disable=unused-argument
            """Mocked function to always raise an exception"""
            raise InvalidKeyError('foo', 'bar')

        with patch('opaque_keys.edx.keys.CourseKey.from_string', side_effect=mock_from_string):
            resp = self.client.get(self.get_url(self.student.username))

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error_code', resp.data)
        self.assertEqual(
            resp.data['error_code'],
            'invalid_course_key'
        )

    def test_course_does_not_exist(self):
        """
        Test that requesting a valid, nonexistent course key returns an error as expected.
        """
        base_url = reverse(
            self.namespaced_url,
            kwargs={
                'course_id': 'course-v1:MITx+8.MechCX+2014_T1',
            }
        )
        url = "{0}?username={1}".format(base_url, self.student.username)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error_code', resp.data)
        self.assertEqual(
            resp.data['error_code'],
            'course_does_not_exist'
        )

    @ddt.data(
        ({'letter_grade': None, 'percent': 0.4, 'passed': False}),
        ({'letter_grade': 'Pass', 'percent': 1, 'passed': True}),
    )
    def test_grade(self, grade):
        """
        Test that the user gets her grade in case she answered tests with an insufficient score.
        """
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            grade_fields = {
                'letter_grade': grade['letter_grade'],
                'percent': grade['percent'],
                'passed': grade['letter_grade'] is not None,

            }
            mock_grade.return_value = MagicMock(**grade_fields)
            resp = self.client.get(self.get_url(self.student.username))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = {
            'username': self.student.username,
            'email': self.student.email,
            'course_id': str(self.course_key),
        }

        expected_data.update(grade)
        self.assertEqual(resp.data, [expected_data])

    def test_staff_can_see_student(self):
        """
        Ensure that staff members can see her student's grades.
        """
        self.client.logout()
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(self.get_url(self.student.username))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = [{
            'username': self.student.username,
            'email': self.student.email,
            'letter_grade': None,
            'percent': 0.0,
            'course_id': str(self.course_key),
            'passed': False
        }]
        self.assertEqual(resp.data, expected_data)


@ddt.ddt
class CourseGradesViewTest(GradeViewTestMixin, APITestCase):
    """
    Tests for grades related to all users in a course
        e.g. /api/grades/v1/courses/{course_id}/
             /api/grades/v1/courses/?course_id={course_id}
    """

    @classmethod
    def setUpClass(cls):
        super(CourseGradesViewTest, cls).setUpClass()
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
        self.client.logout()
        resp = self.client.get(self.get_url())
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student(self):
        resp = self.client.get(self.get_url())
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_does_not_exist(self):
        self.client.logout()
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(course_key='course-v1:MITx+8.MechCX+2014_T1')
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_course_no_enrollments(self):
        self.client.logout()
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(course_key=self.empty_course.id)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_staff_can_get_all_grades(self):
        self.client.logout()
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(self.get_url())

        # this should have permission to access this API endpoint
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = [
            {
                'username': self.student.username,
                'email': self.student.email,
                'course_id': str(self.course.id),
                'passed': False,
                'percent': 0.0,
                'letter_grade': None
            },
            {
                'username': self.other_student.username,
                'email': self.other_student.email,
                'course_id': str(self.course.id),
                'passed': False,
                'percent': 0.0,
                'letter_grade': None
            },
        ]

        self.assertEqual(resp.data, expected_data)
