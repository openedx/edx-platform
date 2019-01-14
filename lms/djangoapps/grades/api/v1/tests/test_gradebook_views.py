"""
Tests for the course grading API view
"""
from __future__ import unicode_literals

import json
from collections import OrderedDict, namedtuple
from datetime import datetime

import ddt
from django.core.urlresolvers import reverse
from freezegun import freeze_time
from mock import MagicMock, patch
from opaque_keys.edx.locator import BlockUsageLocator
from pytz import UTC
from rest_framework import status
from rest_framework.test import APITestCase
from six import text_type

from course_modes.models import CourseMode
from lms.djangoapps.courseware.tests.factories import InstructorFactory, StaffFactory
from lms.djangoapps.grades.api.v1.tests.mixins import GradeViewTestMixin
from lms.djangoapps.grades.api.v1.views import CourseEnrollmentPagination
from lms.djangoapps.grades.config.waffle import WRITABLE_GRADEBOOK, waffle_flags
from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.course_grade import CourseGrade
from lms.djangoapps.grades.models import (
    BlockRecord,
    BlockRecordList,
    PersistentSubsectionGrade,
    PersistentSubsectionGradeOverride,
    PersistentSubsectionGradeOverrideHistory
)
from lms.djangoapps.grades.subsection_grade import ReadSubsectionGrade
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


# pylint: disable=unused-variable
class CourseGradingViewTest(SharedModuleStoreTestCase, APITestCase):
    """
    Test course grading view via a RESTful API
    """
    view_name = 'grades_api:v1:course_gradebook_grading_info'
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(CourseGradingViewTest, cls).setUpClass()

        cls.course = CourseFactory.create(display_name='test course', run="Testing_course")
        cls.course_key = cls.course.id

        cls.password = 'test'
        cls.student = UserFactory(username='dummy', password=cls.password)
        cls.staff = StaffFactory(course_key=cls.course.id, password=cls.password)

        cls.initialize_course(cls.course)

    @classmethod
    def initialize_course(cls, course):
        """
        Sets up the structure of the test course.
        """
        cls.section = ItemFactory.create(
            parent_location=course.location,
            category="chapter",
        )
        cls.subsection1 = ItemFactory.create(
            parent_location=cls.section.location,
            category="sequential",
        )
        unit1 = ItemFactory.create(
            parent_location=cls.subsection1.location,
            category="vertical",
        )
        ItemFactory.create(
            parent_location=unit1.location,
            category="video",
        )
        ItemFactory.create(
            parent_location=unit1.location,
            category="problem",
        )

        cls.subsection2 = ItemFactory.create(
            parent_location=cls.section.location,
            category="sequential",
        )
        unit2 = ItemFactory.create(
            parent_location=cls.subsection2.location,
            category="vertical",
        )
        unit3 = ItemFactory.create(
            parent_location=cls.subsection2.location,
            category="vertical",
        )
        ItemFactory.create(
            parent_location=unit3.location,
            category="video",
        )
        ItemFactory.create(
            parent_location=unit3.location,
            category="video",
        )
        cls.homework = ItemFactory.create(
            parent_location=cls.section.location,
            category="sequential",
            graded=True,
            format='Homework',
        )
        cls.midterm = ItemFactory.create(
            parent_location=cls.section.location,
            category="sequential",
            graded=True,
            format='Midterm Exam',
        )

    def get_url(self, course_id):
        """
        Helper function to create the url
        """
        return reverse(
            self.view_name,
            kwargs={
                'course_id': course_id
            }
        )

    def _get_expected_data(self):
        return {
            'assignment_types': {
                'Final Exam': {
                    'drop_count': 0,
                    'min_count': 1,
                    'short_label': 'Final',
                    'type': 'Final Exam',
                    'weight': 0.4
                },
                'Homework': {
                    'drop_count': 2,
                    'min_count': 12,
                    'short_label': 'HW',
                    'type': 'Homework',
                    'weight': 0.15
                },
                'Lab': {
                    'drop_count': 2,
                    'min_count': 12,
                    'short_label': 'Lab',
                    'type': 'Lab',
                    'weight': 0.15
                },
                'Midterm Exam': {
                    'drop_count': 0,
                    'min_count': 1,
                    'short_label': 'Midterm',
                    'type': 'Midterm Exam',
                    'weight': 0.3
                }
            },
            'subsections': [
                {
                    'assignment_type': None,
                    'display_name': self.subsection1.display_name,
                    'graded': False,
                    'module_id': text_type(self.subsection1.location),
                    'short_label': None
                },
                {
                    'assignment_type': None,
                    'display_name': self.subsection2.display_name,
                    'graded': False,
                    'module_id': text_type(self.subsection2.location),
                    'short_label': None
                },
                {
                    'assignment_type': 'Homework',
                    'display_name': self.homework.display_name,
                    'graded': True,
                    'module_id': text_type(self.homework.location),
                    'short_label': 'HW 01',
                },
                {
                    'assignment_type': 'Midterm Exam',
                    'display_name': self.midterm.display_name,
                    'graded': True,
                    'module_id': text_type(self.midterm.location),
                    'short_label': 'Midterm 01',
                },
            ],
            'grades_frozen': False,
        }

    def test_student_fails(self):
        self.client.login(username=self.student.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_succeeds(self):
        self.client.login(username=self.staff.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = self._get_expected_data()
        self.assertEqual(expected_data, resp.data)

    def test_staff_succeeds_graded_only(self):
        self.client.login(username=self.staff.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key), {'graded_only': True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = self._get_expected_data()
        expected_data['subsections'] = [sub for sub in expected_data['subsections'] if sub['graded']]
        self.assertEqual(expected_data, resp.data)

    def test_course_grade_frozen(self):
        with patch('lms.djangoapps.grades.api.v1.gradebook_views.are_grades_frozen') as mock_frozen_grades:
            mock_frozen_grades.return_value = True
            self.client.login(username=self.staff.username, password=self.password)
            resp = self.client.get(self.get_url(self.course_key))
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            expected_data = self._get_expected_data()
            expected_data['grades_frozen'] = True
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
        cls.course_data = CourseData(None, course=cls.course)
        # we have to force the collection of course data from the block_structure API
        # so that CourseGrade.course_data objects can later have a non-null effective_structure
        _ = cls.course_data.collected_structure

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
        return self.global_staff

    def login_course_staff(self):
        """
        Helper function to login the course staff user, who has permissions to read from the
        Gradebook API.
        """
        course_staff = StaffFactory.create(course_key=self.course_key)
        self._create_user_enrollments(course_staff)
        self.client.login(username=course_staff.username, password=self.password)
        return course_staff

    def login_course_admin(self):
        """
        Helper function to login the course admin user, who has permissions to read from the
        Gradebook API.
        """
        course_admin = InstructorFactory.create(course_key=self.course_key)
        self._create_user_enrollments(course_admin)
        self.client.login(username=course_admin.username, password=self.password)
        return course_admin


@ddt.ddt
class GradebookViewTest(GradebookViewTestBase):
    """
    Tests for the gradebook view.
    """
    @classmethod
    def setUpClass(cls):
        super(GradebookViewTest, cls).setUpClass()
        cls.mock_subsection_grades = {
            cls.subsections[cls.chapter_1.location][0].location: cls.mock_subsection_grade(
                cls.subsections[cls.chapter_1.location][0],
                earned_all=1.0,
                possible_all=2.0,
                earned_graded=1.0,
                possible_graded=2.0,
            ),
            cls.subsections[cls.chapter_1.location][1].location: cls.mock_subsection_grade(
                cls.subsections[cls.chapter_1.location][1],
                earned_all=1.0,
                possible_all=2.0,
                earned_graded=1.0,
                possible_graded=2.0,
            ),
            cls.subsections[cls.chapter_2.location][0].location: cls.mock_subsection_grade(
                cls.subsections[cls.chapter_2.location][0],
                earned_all=1.0,
                possible_all=2.0,
                earned_graded=1.0,
                possible_graded=2.0,
            ),
            cls.subsections[cls.chapter_2.location][1].location: cls.mock_subsection_grade(
                cls.subsections[cls.chapter_2.location][1],
                earned_all=1.0,
                possible_all=2.0,
                earned_graded=1.0,
                possible_graded=2.0,
            ),
        }

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

    @staticmethod
    def mock_subsection_grade(subsection, **kwargs):
        """
        Helper function to mock a subsection grade.
        """
        model = MagicMock(**kwargs)
        if 'override' not in kwargs:
            del model.override
        factory = MagicMock()
        return ReadSubsectionGrade(subsection, model, factory)

    def mock_course_grade(self, user, **kwargs):
        """
        Helper function to return a mock CourseGrade object.
        """
        course_grade = CourseGrade(user=user, course_data=self.course_data, **kwargs)
        course_grade.subsection_grade = lambda key: self.mock_subsection_grades[key]
        return course_grade

    def expected_subsection_grades(self, letter_grade=None):
        """
        Helper function to generate expected subsection detail results.
        """
        return [
            OrderedDict([
                ('attempted', True),
                ('category', 'Homework'),
                ('is_graded', True),
                ('label', 'HW 01'),
                ('letter_grade', letter_grade),
                ('module_id', text_type(self.subsections[self.chapter_1.location][0].location)),
                ('percent', 0.5),
                ('score_earned', 1.0),
                ('score_possible', 2.0),
                ('subsection_name', 'HW 1')
            ]),
            OrderedDict([
                ('attempted', True),
                ('category', 'Lab'),
                ('is_graded', True),
                ('label', 'Lab 01'),
                ('letter_grade', letter_grade),
                ('module_id', text_type(self.subsections[self.chapter_1.location][1].location)),
                ('percent', 0.5),
                ('score_earned', 1.0),
                ('score_possible', 2.0),
                ('subsection_name', 'Lab 1')
            ]),
            OrderedDict([
                ('attempted', True),
                ('category', 'Homework'),
                ('is_graded', True),
                ('label', 'HW 02'),
                ('letter_grade', letter_grade),
                ('module_id', text_type(self.subsections[self.chapter_2.location][0].location)),
                ('percent', 0.5),
                ('score_earned', 1.0),
                ('score_possible', 2.0),
                ('subsection_name', 'HW 2')
            ]),
            OrderedDict([
                ('attempted', True),
                ('category', 'Lab'),
                ('is_graded', True),
                ('label', 'Lab 02'),
                ('letter_grade', letter_grade),
                ('module_id', text_type(self.subsections[self.chapter_2.location][1].location)),
                ('percent', 0.5),
                ('score_earned', 1.0),
                ('score_possible', 2.0),
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

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_gradebook_data_for_course(self, login_method):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.side_effect = [
                self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85),
                self.mock_course_grade(self.other_student, passed=False, letter_grade=None, percent=0.45),
            ]

            with override_waffle_flag(self.waffle_flag, active=True):
                getattr(self, login_method)()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id)
                )
                self._assert_data_all_users(resp)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_gradebook_data_for_single_learner(self, login_method):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85)

            with override_waffle_flag(self.waffle_flag, active=True):
                getattr(self, login_method)()
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
                ])

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                actual_data = dict(resp.data)
                self.assertEqual(expected_results, actual_data)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_gradebook_data_for_single_learner_override(self, login_method):
        """
        Tests that, when a subsection grade that was created from an override, and thus
        does not have a truthy `first_attempted` attribute, is the only grade for a
        user's subsection, we still get data including a non-zero possible score.
        """
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            course_grade = self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85)

            mock_override = MagicMock(
                earned_all_override=1.0,
                possible_all_override=2.0,
                earned_graded_override=1.0,
                possible_graded_override=2.0,
            )
            mock_subsection_grades = {
                self.subsections[self.chapter_1.location][0].location: self.mock_subsection_grade(
                    self.subsections[self.chapter_1.location][0],
                    earned_all=1.0,
                    possible_all=2.0,
                    earned_graded=2.0,
                    possible_graded=2.0,
                    first_attempted=None,
                    override=mock_override,
                ),
                self.subsections[self.chapter_1.location][1].location: self.mock_subsection_grade(
                    self.subsections[self.chapter_1.location][1],
                    earned_all=1.0,
                    possible_all=2.0,
                    earned_graded=2.0,
                    possible_graded=2.0,
                    first_attempted=None,
                    override=mock_override,
                ),
                self.subsections[self.chapter_2.location][0].location: self.mock_subsection_grade(
                    self.subsections[self.chapter_2.location][0],
                    earned_all=1.0,
                    possible_all=2.0,
                    earned_graded=2.0,
                    possible_graded=2.0,
                    first_attempted=None,
                    override=mock_override,
                ),
                self.subsections[self.chapter_2.location][1].location: self.mock_subsection_grade(
                    self.subsections[self.chapter_2.location][1],
                    earned_all=1.0,
                    possible_all=2.0,
                    earned_graded=2.0,
                    possible_graded=2.0,
                    first_attempted=None,
                    override=mock_override,
                ),
            }
            course_grade.subsection_grade = lambda key: mock_subsection_grades[key]
            mock_grade.return_value = course_grade

            with override_waffle_flag(self.waffle_flag, active=True):
                getattr(self, login_method)()
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
                ])

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                actual_data = dict(resp.data)
                self.assertEqual(expected_results, actual_data)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_gradebook_data_filter_username_contains(self, login_method):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(
                self.other_student, passed=True, letter_grade='A', percent=0.85
            )

            with override_waffle_flag(self.waffle_flag, active=True):
                getattr(self, login_method)()
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
                    ]),
                ]

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                actual_data = dict(resp.data)
                self.assertIsNone(actual_data['next'])
                self.assertIsNone(actual_data['previous'])
                self.assertEqual(expected_results, actual_data['results'])

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_gradebook_data_filter_username_contains_no_match(self, login_method):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(
                self.other_student, passed=True, letter_grade='A', percent=0.85
            )

            with override_waffle_flag(self.waffle_flag, active=True):
                getattr(self, login_method)()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id, username_contains='fooooooooooooooooo')
                )
                self._assert_empty_response(resp)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_filter_cohort_id_and_enrollment_mode(self, login_method):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85)

            cohort = CohortFactory(course_id=self.course.id, name="TestCohort", users=[self.student])
            with override_waffle_flag(self.waffle_flag, active=True):
                getattr(self, login_method)()
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
                    ]),
                ]

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                actual_data = dict(resp.data)
                self.assertIsNone(actual_data['next'])
                self.assertIsNone(actual_data['previous'])
                self.assertEqual(expected_results, actual_data['results'])

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_filter_cohort_id_does_not_exist(self, login_method):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.return_value = self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85)

            empty_cohort = CohortFactory(course_id=self.course.id, name="TestCohort", users=[])
            with override_waffle_flag(self.waffle_flag, active=True):
                getattr(self, login_method)()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id) + '?cohort_id={}'.format(empty_cohort.id)
                )
                self._assert_empty_response(resp)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_filter_enrollment_mode(self, login_method):
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
                getattr(self, login_method)()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id) + '?enrollment_mode={}'.format(CourseMode.AUDIT)
                )

                self._assert_data_all_users(resp)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_filter_enrollment_mode_no_students(self, login_method):
        with patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read') as mock_grade:
            mock_grade.side_effect = [
                self.mock_course_grade(self.student, passed=True, letter_grade='A', percent=0.85),
                self.mock_course_grade(self.other_student, passed=False, letter_grade=None, percent=0.45),
            ]

            with override_waffle_flag(self.waffle_flag, active=True):
                getattr(self, login_method)()
                resp = self.client.get(
                    self.get_url(course_key=self.course.id) + '?enrollment_mode={}'.format(CourseMode.VERIFIED)
                )
                self._assert_empty_response(resp)

    @ddt.data(None, 2, 3, 10, 60, 80)
    def test_page_size_parameter(self, page_size):
        user_size = 60
        with patch(
            'lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read'
        ) as mock_grade:
            users = UserFactory.create_batch(user_size)
            mocked_course_grades = []
            for user in users:
                self._create_user_enrollments(user)
                mocked_course_grades.append(self.mock_course_grade(user, passed=True, letter_grade='A', percent=0.85))

            mock_grade.side_effect = mocked_course_grades

            with override_waffle_flag(self.waffle_flag, active=True):
                self.login_staff()
                query = ''
                if page_size:
                    query = '?page_size={}'.format(page_size)
                resp = self.client.get(
                    self.get_url(course_key=self.course.id) + query
                )
                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                actual_data = dict(resp.data)
                expected_page_size = page_size or CourseEnrollmentPagination.page_size
                if expected_page_size > user_size:
                    expected_page_size = user_size
                self.assertEqual(len(actual_data['results']), expected_page_size)


@ddt.ddt
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

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_grades_frozen(self, login_method):
        """
        Should receive a 403 when grades have been frozen for a course.
        """
        with patch('lms.djangoapps.grades.api.v1.gradebook_views.are_grades_frozen', return_value=True):
            with override_waffle_flag(self.waffle_flag, active=True):
                getattr(self, login_method)()
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

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_user_not_enrolled(self, login_method):
        with override_waffle_flag(self.waffle_flag, active=True):
            getattr(self, login_method)()
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

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_user_does_not_exist(self, login_method):
        with override_waffle_flag(self.waffle_flag, active=True):
            getattr(self, login_method)()
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

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_invalid_usage_key(self, login_method):
        with override_waffle_flag(self.waffle_flag, active=True):
            getattr(self, login_method)()
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

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_subsection_does_not_exist(self, login_method):
        """
        When trying to override a grade for a valid usage key that does not exist in the requested course,
        we should get an error reason specifying that the key does not exist in the course.
        """
        with override_waffle_flag(self.waffle_flag, active=True):
            getattr(self, login_method)()
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

    @ddt.data('login_staff', 'login_course_staff', 'login_course_admin')
    def test_override_is_created(self, login_method):
        """
        Test that when we make multiple requests to update grades for the same user/subsection,
        the score from the most recent request is recorded.
        """
        with override_waffle_flag(self.waffle_flag, active=True):
            request_user = getattr(self, login_method)()
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
            # equal to the aggregate of their problem scores (in this case, zeros, since we
            # didn't mock out CourseGradeFactory.read() to return a non-zero score for anything).
            for usage_key, expected_grades, expected_grade_overrides in (
                (
                    self.subsections[self.chapter_1.location][0].location,
                    GradeFields(0, 0, 0, 0),
                    GradeFields(3, 3, 2, 2)
                ),
                (
                    self.subsections[self.chapter_1.location][1].location,
                    GradeFields(0, 0, 0, 0),
                    GradeFields(3, 4, 3, 4)
                ),
            ):
                # this selects related PersistentSubsectionGradeOverride objects.
                grade = PersistentSubsectionGrade.read_grade(
                    user_id=self.student.id,
                    usage_key=usage_key,
                )
                for field_name in expected_grade_overrides._fields:
                    expected_value = getattr(expected_grade_overrides, field_name)
                    self.assertEqual(expected_value, getattr(grade.override, field_name + '_override'))
                for field_name in expected_grades._fields:
                    expected_value = getattr(expected_grades, field_name)
                    self.assertEqual(expected_value, getattr(grade, field_name))

            update_records = PersistentSubsectionGradeOverrideHistory.objects.filter(user=request_user)
            self.assertEqual(update_records.count(), 3)
            for audit_item in update_records:
                self.assertEqual(audit_item.user, request_user)
                self.assertIsNotNone(audit_item.created)
                self.assertEqual(audit_item.feature, PersistentSubsectionGradeOverrideHistory.GRADEBOOK)
                self.assertEqual(audit_item.action, PersistentSubsectionGradeOverrideHistory.CREATE_OR_UPDATE)


@ddt.ddt
class SubsectionGradeViewTest(GradebookViewTestBase):
    """ Test for the audit api call """
    @classmethod
    def setUpClass(cls):
        super(SubsectionGradeViewTest, cls).setUpClass()
        cls.namespaced_url = 'grades_api:v1:course_grade_overrides'
        cls.locator_a = BlockUsageLocator(
            course_key=cls.course_key,
            block_type='problem',
            block_id='block_id_a'
        )
        cls.locator_b = BlockUsageLocator(
            course_key=cls.course_key,
            block_type='problem',
            block_id='block_id_b'
        )
        cls.record_a = BlockRecord(locator=cls.locator_a, weight=1, raw_possible=10, graded=False)
        cls.record_b = BlockRecord(locator=cls.locator_b, weight=1, raw_possible=10, graded=True)
        cls.block_records = BlockRecordList([cls.record_a, cls.record_b], cls.course_key)
        cls.usage_key = cls.subsections[cls.chapter_1.location][0].location
        cls.user_id = 12345
        cls.params = {
            "user_id": cls.user_id,
            "usage_key": cls.usage_key,
            "course_version": "deadbeef",
            "subtree_edited_timestamp": "2016-08-01 18:53:24.354741Z",
            "earned_all": 6.0,
            "possible_all": 12.0,
            "earned_graded": 6.0,
            "possible_graded": 8.0,
            "visible_blocks": cls.block_records,
            "first_attempted": datetime(2000, 1, 1, 12, 30, 45, tzinfo=UTC),
        }
        cls.grade = PersistentSubsectionGrade.update_or_create_grade(**cls.params)

    def get_url(self, subsection_id=None, user_id=None):  # pylint: disable=arguments-differ
        """
        Helper function to create the course gradebook API url.
        """
        base_url = reverse(
            self.namespaced_url,
            kwargs={
                'subsection_id': subsection_id or self.subsection_id,
            }
        )
        return "{0}?user_id={1}".format(base_url, user_id or self.user_id)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_no_override(self, login_method):
        getattr(self, login_method)()

        resp = self.client.get(
            self.get_url(subsection_id=self.usage_key)
        )

        expected_data = {
            'original_grade': OrderedDict([
                ('earned_all', 6.0),
                ('possible_all', 12.0),
                ('earned_graded', 6.0),
                ('possible_graded', 8.0)
            ]),
            'user_id': 12345,
            'override': None,
            'course_id': text_type(self.course_key),
            'subsection_id': text_type(self.usage_key),
            'history': []
        }

        self.assertEqual(expected_data, resp.data)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_with_override_no_history(self, login_method):
        getattr(self, login_method)()

        override = PersistentSubsectionGradeOverride.objects.create(
            grade=self.grade,
            earned_all_override=0.0,
            possible_all_override=12.0,
            earned_graded_override=0.0,
            possible_graded_override=8.0
        )

        resp = self.client.get(
            self.get_url(subsection_id=self.usage_key)
        )

        expected_data = {
            'original_grade': OrderedDict([
                ('earned_all', 6.0),
                ('possible_all', 12.0),
                ('earned_graded', 6.0),
                ('possible_graded', 8.0)
            ]),
            'user_id': 12345,
            'override': OrderedDict([
                ('earned_all_override', 0.0),
                ('possible_all_override', 12.0),
                ('earned_graded_override', 0.0),
                ('possible_graded_override', 8.0)
            ]),
            'course_id': text_type(self.course_key),
            'subsection_id': text_type(self.usage_key),
            'history': []
        }

        self.assertEqual(expected_data, resp.data)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    @freeze_time('2019-01-01')
    def test_with_override_with_history(self, login_method):
        getattr(self, login_method)()

        override = PersistentSubsectionGradeOverride.update_or_create_override(
            requesting_user=self.global_staff,
            subsection_grade_model=self.grade,
            earned_all_override=0.0,
            earned_graded_override=0.0,
            feature=PersistentSubsectionGradeOverrideHistory.GRADEBOOK,
        )

        resp = self.client.get(
            self.get_url(subsection_id=self.usage_key)
        )

        expected_data = {
            'original_grade': OrderedDict([
                ('earned_all', 6.0),
                ('possible_all', 12.0),
                ('earned_graded', 6.0),
                ('possible_graded', 8.0)
            ]),
            'user_id': 12345,
            'override': OrderedDict([
                ('earned_all_override', 0.0),
                ('possible_all_override', 12.0),
                ('earned_graded_override', 0.0),
                ('possible_graded_override', 8.0)
            ]),
            'course_id': text_type(self.course_key),
            'subsection_id': text_type(self.usage_key),
            'history': [{
                'user': self.global_staff.username,
                'comments': None,
                'created': '2019-01-01T00:00:00Z',
                'feature': 'GRADEBOOK',
                'action': 'CREATEORUPDATE'
            }]
        }

        self.assertEqual(expected_data, resp.data)

    @ddt.data(
        'login_staff',
    )
    def test_with_invalid_format_subsection_id(self, login_method):
        getattr(self, login_method)()

        resp = self.client.get(
            self.get_url(subsection_id='notAValidSubectionId')
        )

        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    @ddt.data(
        'login_staff',
    )
    def test_with_invalid_format_user_id(self, login_method):
        getattr(self, login_method)()

        resp = self.client.get(
            self.get_url(subsection_id=self.usage_key, user_id='notAnIntegerUserId')
        )

        self.assertEqual(status.HTTP_404_NOT_FOUND, resp.status_code)

    @ddt.data(
        'login_staff',
        'login_course_admin',
        'login_course_staff',
    )
    def test_with_valid_subsection_id_and_valid_user_id_but_no_record(self, login_method):
        getattr(self, login_method)()

        override = PersistentSubsectionGradeOverride.update_or_create_override(
            requesting_user=self.global_staff,
            subsection_grade_model=self.grade,
            earned_all_override=0.0,
            earned_graded_override=0.0,
            feature=PersistentSubsectionGradeOverrideHistory.GRADEBOOK,
        )

        resp = self.client.get(
            self.get_url(subsection_id=self.usage_key, user_id=6789)
        )

        expected_data = {
            'original_grade': None,
            'user_id': 6789,
            'override': None,
            'course_id': None,
            'subsection_id': text_type(self.usage_key),
            'history': []
        }

        self.assertEqual(expected_data, resp.data)

    def test_with_unauthorized_user(self):
        student = UserFactory(username='dummy', password='test')
        self.client.login(username=student.username, password='test')

        resp = self.client.get(
            self.get_url(subsection_id=self.usage_key)
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
