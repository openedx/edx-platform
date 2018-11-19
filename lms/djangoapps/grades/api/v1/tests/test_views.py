"""
Tests for v1 views
"""
from __future__ import unicode_literals
import json
from collections import OrderedDict, namedtuple
from datetime import datetime

import ddt
from django.urls import reverse
from mock import MagicMock, patch
from opaque_keys import InvalidKeyError
from pytz import UTC
from rest_framework import status
from rest_framework.test import APITestCase
from six import text_type

from course_modes.models import CourseMode
from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory
from lms.djangoapps.grades.api.v1.views import CourseGradesView
from lms.djangoapps.grades.config.waffle import waffle_flags, WRITABLE_GRADEBOOK
from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.course_grade import CourseGrade
from lms.djangoapps.grades.models import PersistentSubsectionGrade, PersistentSubsectionGradeOverrideHistory
from lms.djangoapps.grades.subsection_grade import ReadSubsectionGrade
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from openedx.core.djangoapps.user_authn.tests.utils import AuthAndScopesTestMixin
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
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

    def _create_user_enrollments(self, *users):
        date = datetime(2013, 1, 22, tzinfo=UTC)
        for user in users:
            CourseEnrollmentFactory(
                course_id=self.course.id,
                user=user,
                created=date,
            )

    def setUp(self):
        super(GradeViewTestMixin, self).setUp()
        self.password = 'test'
        self.global_staff = GlobalStaffFactory.create()
        self.student = UserFactory(password=self.password, username='student')
        self.other_student = UserFactory(password=self.password, username='other_student')
        self._create_user_enrollments(self.student, self.other_student)

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
class SingleUserGradesTests(GradeViewTestMixin, AuthAndScopesTestMixin, APITestCase):
    """
    Tests for grades related to a course and specific user
        e.g. /api/grades/v1/courses/{course_id}/?username={username}
             /api/grades/v1/courses/?course_id={course_id}&username={username}
    """
    default_scopes = CourseGradesView.required_scopes

    @classmethod
    def setUpClass(cls):
        super(SingleUserGradesTests, cls).setUpClass()
        cls.namespaced_url = 'grades_api:v1:course_grades'

    def get_url(self, username):
        """ This method is required by AuthAndScopesTestMixin. """
        base_url = reverse(
            self.namespaced_url,
            kwargs={
                'course_id': self.course_key,
            }
        )
        return "{0}?username={1}".format(base_url, username)

    def assert_success_response_for_student(self, response):
        """ This method is required by AuthAndScopesTestMixin. """
        expected_data = [{
            'username': self.student.username,
            'email': self.student.email,
            'letter_grade': None,
            'percent': 0.0,
            'course_id': str(self.course_key),
            'passed': False
        }]
        self.assertEqual(response.data, expected_data)

    def test_nonexistent_user(self):
        """
        Test that a request for a nonexistent username returns an error.
        """
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(self.get_url('IDoNotExist'))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_self_get_grade_not_enrolled(self):
        """
        Test that a user receives an error if she requests
        her own grade in a course where she is not enrolled.
        """
        # a user not enrolled in the course cannot request her grade
        unenrolled_user = UserFactory(password=self.password)
        self.client.login(username=unenrolled_user.username, password=self.password)
        resp = self.client.get(self.get_url(unenrolled_user.username))
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
        self.client.login(username=self.student.username, password=self.password)
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

        self.client.login(username=self.student.username, password=self.password)
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
        self.client.login(username=self.student.username, password=self.password)
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
        self.client.login(username=self.student.username, password=self.password)
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
        resp = self.client.get(self.get_url())
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student(self):
        self.client.login(username=self.student.username, password=self.password)
        resp = self.client.get(self.get_url())
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_does_not_exist(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(course_key='course-v1:MITx+8.MechCX+2014_T1')
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_course_no_enrollments(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(
            self.get_url(course_key=self.empty_course.id)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = OrderedDict([
            ('next', None),
            ('previous', None),
            ('results', []),
        ])
        self.assertEqual(expected_data, resp.data)

    def test_staff_can_get_all_grades(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        resp = self.client.get(self.get_url())

        # this should have permission to access this API endpoint
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = OrderedDict([
            ('next', None),
            ('previous', None),
            ('results', [
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
            ]),
        ])

        self.assertEqual(expected_data, resp.data)


class GradebookViewTestBase(GradeViewTestMixin, APITestCase):
    """
    Base class for the gradebook GET and POST view tests.
    """
    @classmethod
    def setUpClass(cls):
        super(GradebookViewTestBase, cls).setUpClass()
        cls.namespaced_url = 'grades_api:v1:course_gradebook'
        cls.waffle_flag = waffle_flags()[WRITABLE_GRADEBOOK]

        cls.course = CourseFactory.create(display_name='test-course', run='run-1')
        cls.course_key = cls.course.id
        cls.course_overview = CourseOverviewFactory.create(id=cls.course.id)

        cls.chapter_1 = ItemFactory.create(
            category='chapter',
            parent_location=cls.course.location,
            display_name="Chapter 1",
        )
        cls.chapter_2 = ItemFactory.create(
            category='chapter',
            parent_location=cls.course.location,
            display_name="Chapter 2",
        )
        cls.subsections = {
            cls.chapter_1.location: [
                ItemFactory.create(
                    category='sequential',
                    parent_location=cls.chapter_1.location,
                    due=datetime(2017, 12, 18, 11, 30, 00),
                    display_name='HW 1',
                    format='Homework',
                    graded=True,
                ),
                ItemFactory.create(
                    category='sequential',
                    parent_location=cls.chapter_1.location,
                    due=datetime(2017, 12, 18, 11, 30, 00),
                    display_name='Lab 1',
                    format='Lab',
                    graded=True,
                ),
            ],
            cls.chapter_2.location: [
                ItemFactory.create(
                    category='sequential',
                    parent_location=cls.chapter_2.location,
                    due=datetime(2017, 12, 18, 11, 30, 00),
                    display_name='HW 2',
                    format='Homework',
                    graded=True,
                ),
                ItemFactory.create(
                    category='sequential',
                    parent_location=cls.chapter_2.location,
                    due=datetime(2017, 12, 18, 11, 30, 00),
                    display_name='Lab 2',
                    format='Lab',
                    graded=True,
                ),
            ],
        }

    def get_url(self, course_key=None):
        """
        Helper function to create the course gradebook API url.
        """
        return reverse(
            self.namespaced_url,
            kwargs={
                'course_id': course_key or self.course_key,
            }
        )

    def login_staff(self):
        """
        Helper function to login the global staff user, who has permissions to read from the
        Gradebook API.
        """
        self.client.login(username=self.global_staff.username, password=self.password)


class GradebookViewTest(GradebookViewTestBase):
    """
    Tests for the gradebook view.
    """
    def get_url(self, course_key=None, username=None, username_contains=None):  # pylint: disable=arguments-differ
        """
        Helper function to create the course gradebook API read url.
        """
        base_url = super(GradebookViewTest, self).get_url(course_key)
        if username:
            return "{0}?username={1}".format(base_url, username)
        if username_contains:
            return "{0}?username_contains={1}".format(base_url, username_contains)
        return base_url

    def mock_subsection_grade(self, subsection, **kwargs):
        """
        Helper function to mock a subsection grade.
        """
        model = MagicMock(**kwargs)
        factory = MagicMock()
        return ReadSubsectionGrade(subsection, model, factory)

    def mock_course_grade(self, user, **kwargs):
        """
        Helper function to return a mock CourseGrade object.
        """
        course_data = CourseData(user, course=self.course)
        course_grade = CourseGrade(user=user, course_data=course_data, **kwargs)
        course_grade.chapter_grades = OrderedDict([
            (self.chapter_1.location, {
                'sections': [
                    self.mock_subsection_grade(
                        self.subsections[self.chapter_1.location][0],
                        earned_all=1.0,
                        possible_all=2.0,
                        earned_graded=1.0,
                        possible_graded=2.0,
                    ),
                    self.mock_subsection_grade(
                        self.subsections[self.chapter_1.location][1],
                        earned_all=1.0,
                        possible_all=2.0,
                        earned_graded=1.0,
                        possible_graded=2.0,
                    ),
                ],
                'display_name': 'Chapter 1',
            }),
            (self.chapter_2.location, {
                'sections': [
                    self.mock_subsection_grade(
                        self.subsections[self.chapter_2.location][0],
                        earned_all=1.0,
                        possible_all=2.0,
                        earned_graded=1.0,
                        possible_graded=2.0,
                    ),
                    self.mock_subsection_grade(
                        self.subsections[self.chapter_2.location][1],
                        earned_all=1.0,
                        possible_all=2.0,
                        earned_graded=1.0,
                        possible_graded=2.0,
                    ),
                ],
                'display_name': 'Chapter 2',
            }),
        ])
        return course_grade

    def expected_subsection_grades(self, letter_grade=None):
        """
        Helper function to generate expected subsection detail results.
        """
        return [
            OrderedDict([
                ('are_grades_published', True),
                ('auto_grade', False),
                ('category', 'Homework'),
                ('chapter_name', 'Chapter 1'),
                ('comment', ''),
                ('detail', ''),
                ('displayed_value', '0.50'),
                ('is_graded', True),
                ('grade_description', '(1.00/2.00)'),
                ('is_ag', False),
                ('is_average', False),
                ('is_manually_graded', False),
                ('label', 'HW 01'),
                ('letter_grade', letter_grade),
                ('module_id', text_type(self.subsections[self.chapter_1.location][0].location)),
                ('percent', 0.5),
                ('score_earned', 1.0),
                ('score_possible', 2.0),
                ('section_block_id', text_type(self.chapter_1.location)),
                ('subsection_name', 'HW 1')
            ]),
            OrderedDict([
                ('are_grades_published', True),
                ('auto_grade', False),
                ('category', 'Lab'),
                ('chapter_name', 'Chapter 1'),
                ('comment', ''),
                ('detail', ''),
                ('displayed_value', '0.50'),
                ('is_graded', True),
                ('grade_description', '(1.00/2.00)'),
                ('is_ag', False),
                ('is_average', False),
                ('is_manually_graded', False),
                ('label', 'Lab 01'),
                ('letter_grade', letter_grade),
                ('module_id', text_type(self.subsections[self.chapter_1.location][1].location)),
                ('percent', 0.5),
                ('score_earned', 1.0),
                ('score_possible', 2.0),
                ('section_block_id', text_type(self.chapter_1.location)),
                ('subsection_name', 'Lab 1')
            ]),
            OrderedDict([
                ('are_grades_published', True),
                ('auto_grade', False),
                ('category', 'Homework'),
                ('chapter_name', 'Chapter 2'),
                ('comment', ''),
                ('detail', ''),
                ('displayed_value', '0.50'),
                ('is_graded', True),
                ('grade_description', '(1.00/2.00)'),
                ('is_ag', False),
                ('is_average', False),
                ('is_manually_graded', False),
                ('label', 'HW 02'),
                ('letter_grade', letter_grade),
                ('module_id', text_type(self.subsections[self.chapter_2.location][0].location)),
                ('percent', 0.5),
                ('score_earned', 1.0),
                ('score_possible', 2.0),
                ('section_block_id', text_type(self.chapter_2.location)),
                ('subsection_name', 'HW 2')
            ]),
            OrderedDict([
                ('are_grades_published', True),
                ('auto_grade', False),
                ('category', 'Lab'),
                ('chapter_name', 'Chapter 2'),
                ('comment', ''),
                ('detail', ''),
                ('displayed_value', '0.50'),
                ('is_graded', True),
                ('grade_description', '(1.00/2.00)'),
                ('is_ag', False),
                ('is_average', False),
                ('is_manually_graded', False),
                ('label', 'Lab 02'),
                ('letter_grade', letter_grade),
                ('module_id', text_type(self.subsections[self.chapter_2.location][1].location)),
                ('percent', 0.5),
                ('score_earned', 1.0),
                ('score_possible', 2.0),
                ('section_block_id', text_type(self.chapter_2.location)),
                ('subsection_name', 'Lab 2')
            ]),
        ]

    def _assert_data_all_users(self, response):
        """
        Helper method to assert that self.student and self.other_student
        have the expected gradebook data.
        """
        expected_results = [
            OrderedDict([
                ('course_id', text_type(self.course.id)),
                ('email', self.student.email),
                ('user_id', self.student.id),
                ('username', self.student.username),
                ('full_name', self.student.get_full_name()),
                ('passed', True),
                ('percent', 0.85),
                ('letter_grade', 'A'),
                ('progress_page_url', reverse(
                    'student_progress',
                    kwargs=dict(course_id=text_type(self.course.id), student_id=self.student.id)
                )),
                ('section_breakdown', self.expected_subsection_grades(letter_grade='A')),
                ('aggregates', {
                    'Lab': {
                        'score_earned': 2.0,
                        'score_possible': 4.0,
                    },
                    'Homework': {
                        'score_earned': 2.0,
                        'score_possible': 4.0,
                    },
                }),
            ]),
            OrderedDict([
                ('course_id', text_type(self.course.id)),
                ('email', self.other_student.email),
                ('user_id', self.other_student.id),
                ('username', self.other_student.username),
                ('full_name', self.other_student.get_full_name()),
                ('passed', False),
                ('percent', 0.45),
                ('letter_grade', None),
                ('progress_page_url', reverse(
                    'student_progress',
                    kwargs=dict(course_id=text_type(self.course.id), student_id=self.other_student.id)
                )),
                ('section_breakdown', self.expected_subsection_grades()),
                ('aggregates', {
                    'Lab': {
                        'score_earned': 2.0,
                        'score_possible': 4.0,
                    },
                    'Homework': {
                        'score_earned': 2.0,
                        'score_possible': 4.0,
                    },
                }),
            ]),
        ]

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        actual_data = dict(response.data)
        self.assertIsNone(actual_data['next'])
        self.assertIsNone(actual_data['previous'])
        self.assertEqual(expected_results, actual_data['results'])

    def _assert_empty_response(self, response):
        """
        Helper method for assertions about OK, empty responses.
        """
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        actual_data = dict(response.data)
        self.assertIsNone(actual_data['next'])
        self.assertIsNone(actual_data['previous'])
        self.assertEqual([], actual_data['results'])

    def test_feature_not_enabled(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        with override_waffle_flag(self.waffle_flag, active=False):
            resp = self.client.get(
                self.get_url(course_key=self.empty_course.id)
            )
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_anonymous(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            resp = self.client.get(self.get_url())
            self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

    def test_student(self):
        self.client.login(username=self.student.username, password=self.password)
        with override_waffle_flag(self.waffle_flag, active=True):
            resp = self.client.get(self.get_url())
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_course_does_not_exist(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            resp = self.client.get(
                self.get_url(course_key='course-v1:MITx+8.MechCX+2014_T1')
            )
            self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_user_does_not_exist(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            resp = self.client.get(
                self.get_url(course_key=self.course.id, username='not-a-real-user')
            )
            self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_user_not_enrolled(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            resp = self.client.get(
                self.get_url(course_key=self.empty_course.id, username=self.student.username)
            )
            self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_course_no_enrollments(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            resp = self.client.get(
                self.get_url(course_key=self.empty_course.id)
            )
            self._assert_empty_response(resp)

    def test_gradebook_data_for_course(self):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.side_effect = [
                self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85),
                self.mock_course_grade(self.other_student, passed=False, letter_grade=None, percent=0.45),
            ]

            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id)
                )
                self._assert_data_all_users(resp)

    def test_gradebook_data_for_single_learner(self):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85)

            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id, username=self.student.username)
                )
                expected_results = OrderedDict([
                    ('course_id', text_type(self.course.id)),
                    ('email', self.student.email),
                    ('user_id', self.student.id),
                    ('username', self.student.username),
                    ('full_name', self.student.get_full_name()),
                    ('passed', True),
                    ('percent', 0.85),
                    ('letter_grade', 'A'),
                    ('progress_page_url', reverse(
                        'student_progress',
                        kwargs=dict(course_id=text_type(self.course.id), student_id=self.student.id)
                    )),
                    ('section_breakdown', self.expected_subsection_grades(letter_grade='A')),
                    ('aggregates', {
                        'Lab': {
                            'score_earned': 2.0,
                            'score_possible': 4.0,
                        },
                        'Homework': {
                            'score_earned': 2.0,
                            'score_possible': 4.0,
                        },
                    }),
                ])

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                actual_data = dict(resp.data)
                self.assertEqual(expected_results, actual_data)

    def test_gradebook_data_filter_username_contains(self):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(
                self.other_student, passed=True, letter_grade='A', percent=0.85
            )

            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id, username_contains='other')
                )
                expected_results = [
                    OrderedDict([
                        ('course_id', text_type(self.course.id)),
                        ('email', self.other_student.email),
                        ('user_id', self.other_student.id),
                        ('username', self.other_student.username),
                        ('full_name', self.other_student.get_full_name()),
                        ('passed', True),
                        ('percent', 0.85),
                        ('letter_grade', 'A'),
                        ('progress_page_url', reverse(
                            'student_progress',
                            kwargs=dict(course_id=text_type(self.course.id), student_id=self.other_student.id)
                        )),
                        ('section_breakdown', self.expected_subsection_grades(letter_grade='A')),
                        ('aggregates', {
                            'Lab': {
                                'score_earned': 2.0,
                                'score_possible': 4.0,
                            },
                            'Homework': {
                                'score_earned': 2.0,
                                'score_possible': 4.0,
                            },
                        }),
                    ]),
                ]

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                actual_data = dict(resp.data)
                self.assertIsNone(actual_data['next'])
                self.assertIsNone(actual_data['previous'])
                self.assertEqual(expected_results, actual_data['results'])

    def test_gradebook_data_filter_username_contains_no_match(self):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(
                self.other_student, passed=True, letter_grade='A', percent=0.85
            )

            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id, username_contains='fooooooooooooooooo')
                )
                self._assert_empty_response(resp)

    def test_filter_cohort_id_and_enrollment_mode(self):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85)

            cohort = CohortFactory(course_id=self.course.id, name="TestCohort", users=[self.student])
            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                # both of our test users are in the audit track, so this is functionally equivalent
                # to just `?cohort_id=cohort.id`.
                query = '?cohort_id={}&enrollment_mode={}'.format(cohort.id, CourseMode.AUDIT)
                resp = self.client.get(
                    self.get_url(course_key=self.course.id) + query
                )

                expected_results = [
                    OrderedDict([
                        ('course_id', text_type(self.course.id)),
                        ('email', self.student.email),
                        ('user_id', self.student.id),
                        ('username', self.student.username),
                        ('full_name', self.student.get_full_name()),
                        ('passed', True),
                        ('percent', 0.85),
                        ('letter_grade', 'A'),
                        ('progress_page_url', reverse(
                            'student_progress',
                            kwargs=dict(course_id=text_type(self.course.id), student_id=self.student.id)
                        )),
                        ('section_breakdown', self.expected_subsection_grades(letter_grade='A')),
                        ('aggregates', {
                            'Lab': {
                                'score_earned': 2.0,
                                'score_possible': 4.0,
                            },
                            'Homework': {
                                'score_earned': 2.0,
                                'score_possible': 4.0,
                            },
                        }),
                    ]),
                ]

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                actual_data = dict(resp.data)
                self.assertIsNone(actual_data['next'])
                self.assertIsNone(actual_data['previous'])
                self.assertEqual(expected_results, actual_data['results'])

    def test_filter_cohort_id_does_not_exist(self):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85)

            empty_cohort = CohortFactory(course_id=self.course.id, name="TestCohort", users=[])
            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id) + '?cohort_id={}'.format(empty_cohort.id)
                )
                self._assert_empty_response(resp)

    def test_filter_enrollment_mode(self):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.side_effect = [
                self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85),
                self.mock_course_grade(self.other_student, passed=False, letter_grade=None, percent=0.45),
            ]

            # Enroll a verified student, for whom data should not be returned.
            verified_student = UserFactory()
            _ = CourseEnrollmentFactory(
                course_id=self.course.id,
                user=verified_student,
                created=datetime(2013, 1, 1, tzinfo=UTC),
                mode=CourseMode.VERIFIED,
            )
            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id) + '?enrollment_mode={}'.format(CourseMode.AUDIT)
                )

                self._assert_data_all_users(resp)

    def test_filter_enrollment_mode_no_students(self):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.side_effect = [
                self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85),
                self.mock_course_grade(self.other_student, passed=False, letter_grade=None, percent=0.45),
            ]

            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id) + '?enrollment_mode={}'.format(CourseMode.VERIFIED)
                )
                self._assert_empty_response(resp)

    def test_ungraded_subsection(self):
        """
        Tests that an ungraded subsection is returned with the response data, and that the default
        subsection label is returned (since no short label is generated for ungraded content).
        """
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            course_grade = self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85)
            ungraded_subsection = ItemFactory.create(
                category='sequential',
                parent_location=self.chapter_2.location,
                due=datetime(2017, 12, 18, 11, 30, 00),
                display_name='HW 3',
                format='Homework',
                graded=False,
            )
            subsection_grade = self.mock_subsection_grade(
                ungraded_subsection,
                earned_all=0.0,
                possible_all=1.0,
                earned_graded=0.0,
                possible_graded=0.0,
            )
            course_grade.chapter_grades[self.chapter_2.location]['sections'].append(subsection_grade)
            mock_grade.return_value = course_grade

            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id, username=self.student.username)
                )

                expected_subsection_breakdown = self.expected_subsection_grades(letter_grade='A')
                expected_subsection_breakdown.append(OrderedDict([
                    ('are_grades_published', True),
                    ('auto_grade', False),
                    ('category', 'Homework'),
                    ('chapter_name', 'Chapter 2'),
                    ('comment', ''),
                    ('detail', ''),
                    ('displayed_value', '0.00'),
                    ('is_graded', False),
                    ('grade_description', '(0.00/0.00)'),
                    ('is_ag', False),
                    ('is_average', False),
                    ('is_manually_graded', False),
                    ('label', 'HW 03'),
                    ('letter_grade', 'A'),
                    ('module_id', text_type(ungraded_subsection.location)),
                    ('percent', 0.0),
                    ('score_earned', 0.0),
                    ('score_possible', 0.0),
                    ('section_block_id', text_type(self.chapter_2.location)),
                    ('subsection_name', 'HW 3')
                ]))

                expected_results = OrderedDict([
                    ('course_id', text_type(self.course.id)),
                    ('email', self.student.email),
                    ('user_id', self.student.id),
                    ('username', self.student.username),
                    ('full_name', self.student.get_full_name()),
                    ('passed', True),
                    ('percent', 0.85),
                    ('letter_grade', 'A'),
                    ('progress_page_url', reverse(
                        'student_progress',
                        kwargs=dict(course_id=text_type(self.course.id), student_id=self.student.id)
                    )),
                    ('section_breakdown', expected_subsection_breakdown),
                    ('aggregates', {
                        'Lab': {
                            'score_earned': 2.0,
                            'score_possible': 4.0,
                        },
                        'Homework': {
                            'score_earned': 2.0,
                            'score_possible': 4.0,
                        },
                    }),
                ])

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                actual_data = dict(resp.data)
                self.assertEqual(expected_results, actual_data)


class GradebookBulkUpdateViewTest(GradebookViewTestBase):
    """
    Tests for the gradebook bulk-update view.
    """
    @classmethod
    def setUpClass(cls):
        super(GradebookBulkUpdateViewTest, cls).setUpClass()
        cls.namespaced_url = 'grades_api:v1:course_gradebook_bulk_update'

    def test_feature_not_enabled(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        with override_waffle_flag(self.waffle_flag, active=False):
            resp = self.client.post(
                self.get_url(course_key=self.empty_course.id)
            )
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_anonymous(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            resp = self.client.post(self.get_url())
            self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

    def test_student(self):
        self.client.login(username=self.student.username, password=self.password)
        with override_waffle_flag(self.waffle_flag, active=True):
            resp = self.client.post(self.get_url())
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_course_does_not_exist(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            resp = self.client.post(
                self.get_url(course_key='course-v1:MITx+8.MechCX+2014_T1')
            )
            self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    def test_grades_frozen(self):
        """
        Should receive a 403 when grades have been frozen for a course.
        """
        with patch('lms.djangoapps.grades.api.v1.views.are_grades_frozen', return_value=True):
            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                post_data = [
                    {
                        'user_id': self.student.id,
                        'usage_id': text_type(self.subsections[self.chapter_1.location][0].location),
                        'grade': {},  # doesn't matter what we put here.
                    }
                ]

                resp = self.client.post(
                    self.get_url(),
                    data=json.dumps(post_data),
                    content_type='application/json',
                )
                self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_user_not_enrolled(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            unenrolled_student = UserFactory()
            post_data = [
                {
                    'user_id': unenrolled_student.id,
                    'usage_id': text_type(self.subsections[self.chapter_1.location][0].location),
                    'grade': {},  # doesn't matter what we put here.
                }
            ]

            resp = self.client.post(
                self.get_url(),
                data=json.dumps(post_data),
                content_type='application/json',
            )

            expected_data = [
                {
                    'user_id': unenrolled_student.id,
                    'usage_id': text_type(self.subsections[self.chapter_1.location][0].location),
                    'success': False,
                    'reason': 'CourseEnrollment matching query does not exist.',
                },
            ]
            self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY, resp.status_code)
            self.assertEqual(expected_data, resp.data)

    def test_user_does_not_exist(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            post_data = [
                {
                    'user_id': -123,
                    'usage_id': text_type(self.subsections[self.chapter_1.location][0].location),
                    'grade': {},  # doesn't matter what we put here.
                }
            ]

            resp = self.client.post(
                self.get_url(),
                data=json.dumps(post_data),
                content_type='application/json',
            )

            expected_data = [
                {
                    'user_id': -123,
                    'usage_id': text_type(self.subsections[self.chapter_1.location][0].location),
                    'success': False,
                    'reason': 'User matching query does not exist.',
                },
            ]
            self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY, resp.status_code)
            self.assertEqual(expected_data, resp.data)

    def test_invalid_usage_key(self):
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            post_data = [
                {
                    'user_id': self.student.id,
                    'usage_id': 'not-a-valid-usage-key',
                    'grade': {},  # doesn't matter what we put here.
                }
            ]

            resp = self.client.post(
                self.get_url(),
                data=json.dumps(post_data),
                content_type='application/json',
            )

            expected_data = [
                {
                    'user_id': self.student.id,
                    'usage_id': 'not-a-valid-usage-key',
                    'success': False,
                    'reason': "<class 'opaque_keys.edx.locator.BlockUsageLocator'>: not-a-valid-usage-key",
                },
            ]
            self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY, resp.status_code)
            self.assertEqual(expected_data, resp.data)

    def test_subsection_does_not_exist(self):
        """
        When trying to override a grade for a valid usage key that does not exist in the requested course,
        we should get an error reason specifying that the key does not exist in the course.
        """
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            usage_id = 'block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow'
            post_data = [
                {
                    'user_id': self.student.id,
                    'usage_id': usage_id,
                    'grade': {},  # doesn't matter what we put here.
                }
            ]

            resp = self.client.post(
                self.get_url(),
                data=json.dumps(post_data),
                content_type='application/json',
            )

            expected_data = [
                {
                    'user_id': self.student.id,
                    'usage_id': usage_id,
                    'success': False,
                    'reason': 'usage_key {} does not exist in this course.'.format(usage_id),
                },
            ]
            self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY, resp.status_code)
            self.assertEqual(expected_data, resp.data)

    def test_override_is_created(self):
        """
        Test that when we make multiple requests to update grades for the same user/subsection,
        the score from the most recent request is recorded.
        """
        with override_waffle_flag(self.waffle_flag, active=True):
            self.login_staff()
            post_data = [
                {
                    'user_id': self.student.id,
                    'usage_id': text_type(self.subsections[self.chapter_1.location][0].location),
                    'grade': {
                        'earned_all_override': 3,
                        'possible_all_override': 3,
                        'earned_graded_override': 2,
                        'possible_graded_override': 2,
                    },
                },
                {
                    'user_id': self.student.id,
                    'usage_id': text_type(self.subsections[self.chapter_1.location][1].location),
                    'grade': {
                        'earned_all_override': 1,
                        'possible_all_override': 4,
                        'earned_graded_override': 1,
                        'possible_graded_override': 4,
                    },
                }
            ]

            resp = self.client.post(
                self.get_url(),
                data=json.dumps(post_data),
                content_type='application/json',
            )

            expected_data = [
                {
                    'user_id': self.student.id,
                    'usage_id': text_type(self.subsections[self.chapter_1.location][0].location),
                    'success': True,
                    'reason': None,
                },
                {
                    'user_id': self.student.id,
                    'usage_id': text_type(self.subsections[self.chapter_1.location][1].location),
                    'success': True,
                    'reason': None,
                },
            ]
            self.assertEqual(status.HTTP_202_ACCEPTED, resp.status_code)
            self.assertEqual(expected_data, resp.data)

            second_post_data = [
                {
                    'user_id': self.student.id,
                    'usage_id': text_type(self.subsections[self.chapter_1.location][1].location),
                    'grade': {
                        'earned_all_override': 3,
                        'possible_all_override': 4,
                        'earned_graded_override': 3,
                        'possible_graded_override': 4,
                    },
                },
            ]

            self.client.post(
                self.get_url(),
                data=json.dumps(second_post_data),
                content_type='application/json',
            )

            GradeFields = namedtuple('GradeFields', ['earned_all', 'possible_all', 'earned_graded', 'possible_graded'])

            # We should now have PersistentSubsectionGradeOverride records corresponding to
            # our bulk-update request, and PersistentSubsectionGrade records with grade values
            # equal to those of the override.
            for usage_key, expected_grades in (
                (self.subsections[self.chapter_1.location][0].location, GradeFields(3, 3, 2, 2)),
                (self.subsections[self.chapter_1.location][1].location, GradeFields(3, 4, 3, 4)),
            ):
                # this selects related PersistentSubsectionGradeOverride objects.
                grade = PersistentSubsectionGrade.read_grade(
                    user_id=self.student.id,
                    usage_key=usage_key,
                )
                for field_name in expected_grades._fields:
                    expected_value = getattr(expected_grades, field_name)
                    self.assertEqual(expected_value, getattr(grade, field_name))
                    self.assertEqual(expected_value, getattr(grade.override, field_name + '_override'))

            update_records = PersistentSubsectionGradeOverrideHistory.objects.filter(user=self.global_staff)
            self.assertEqual(update_records.count(), 3)
            for audit_item in update_records:
                self.assertEqual(audit_item.user, self.global_staff)
                self.assertIsNotNone(audit_item.created)
                self.assertEqual(audit_item.feature, PersistentSubsectionGradeOverrideHistory.GRADEBOOK)
                self.assertEqual(audit_item.action, PersistentSubsectionGradeOverrideHistory.CREATE_OR_UPDATE)
