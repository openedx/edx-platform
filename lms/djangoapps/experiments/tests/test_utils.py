"""
Tests of experiment functionality
"""
from unittest import TestCase
from lms.djangoapps.experiments.utils import is_enrolled_in_course_run
from opaque_keys.edx.keys import CourseKey


class ExperimentUtilsTests(TestCase):
    """
    Tests of experiment functionality
    """
    def test_valid_course_run_key_enrollment(self):
        course_run = {
            'key': 'course-v1:DelftX+NGIx+RA0',
        }
        enrollment_ids = {CourseKey.from_string('course-v1:DelftX+NGIx+RA0')}
        self.assertTrue(is_enrolled_in_course_run(course_run, enrollment_ids))

    def test_invalid_course_run_key_enrollment(self):
        course_run = {
            'key': 'cr_key',
        }
        enrollment_ids = {CourseKey.from_string('course-v1:DelftX+NGIx+RA0')}
        self.assertFalse(is_enrolled_in_course_run(course_run, enrollment_ids))
