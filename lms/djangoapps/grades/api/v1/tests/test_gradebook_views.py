"""
Tests for the course grading API view
"""
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from six import text_type

from lms.djangoapps.courseware.tests.factories import StaffFactory
from student.tests.factories import UserFactory
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
        course.self_paced = True

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

    def test_student_fails(self):
        self.client.login(username=self.student.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_succeeds(self):
        self.client.login(username=self.staff.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = {
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
            ]
        }
        self.assertEqual(expected_data, resp.data)

    def test_staff_succeeds_graded_only(self):
        self.client.login(username=self.staff.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key), {'graded_only': True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = {
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
            ]
        }
        self.assertEqual(expected_data, resp.data)
