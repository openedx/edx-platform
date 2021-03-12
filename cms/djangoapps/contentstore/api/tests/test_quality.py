"""
Tests for the course import API views
"""


from rest_framework import status

from .base import BaseCourseViewTest


class CourseQualityViewTest(BaseCourseViewTest):
    """
    Test course quality view via a RESTful API
    """
    view_name = 'courses_api:course_quality'

    def test_staff_succeeds(self):
        self.client.login(username=self.staff.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key), {'all': 'true'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected_data = {
            'units': {
                'num_blocks': {
                    'max': 2,
                    'mean': 1.0,
                    'median': 2.0,
                    'mode': 2.0,
                    'min': 0,
                },
                'total_visible': 3,
            },
            'videos': {
                'durations': {
                    'max': None,
                    'mean': None,
                    'median': None,
                    'mode': None,
                    'min': None,
                },
                'num_mobile_encoded': 0,
                'num_with_val_id': 0,
                'total_number': 3,
            },
            'sections': {
                'number_with_highlights': 0,
                'total_visible': 1,
                'total_number': 1,
                'highlights_enabled': False,
                'highlights_active_for_course': False,
            },
            'subsections': {
                'num_with_one_block_type': 1,
                'num_block_types': {
                    'max': 2,
                    'mean': 2.0,
                    'median': 2.0,
                    'mode': 1.0,
                    'min': 1,
                },
                'total_visible': 2,
            },
            'is_self_paced': True,
        }
        self.assertDictEqual(resp.data, expected_data)

    def test_student_fails(self):
        self.client.login(username=self.student.username, password=self.password)
        resp = self.client.get(self.get_url(self.course_key))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
