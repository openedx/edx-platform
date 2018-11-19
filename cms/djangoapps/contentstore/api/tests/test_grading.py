"""
Tests for the course grading API view
"""
from rest_framework import status
from six import text_type

from xmodule.modulestore.tests.factories import ItemFactory

from .base import BaseCourseViewTest


class CourseGradingViewTest(BaseCourseViewTest):
    """
    Test course grading view via a RESTful API
    """
    view_name = 'courses_api:course_grading'

    @classmethod
    def setUpClass(cls):
        super(CourseGradingViewTest, cls).setUpClass()
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
