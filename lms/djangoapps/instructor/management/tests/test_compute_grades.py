# coding=utf-8

"""Tests for Django instructor management commands"""

from unittest import TestCase

from django.core.management import call_command
from mock import Mock

from instructor.offline_gradecalc import offline_grade_calculation  # pylint: disable=unused-import
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator


class InstructorCommandsTest(TestCase):
    """Unittest subclass for instructor module management commands."""

    def test_compute_grades_command(self):
        course_id = 'MITx/0.0001/2016_Fall'
        offline_grade_calculation = Mock()  # pylint: disable=redefined-outer-name
        CourseKey.from_string = Mock(return_value=CourseLocator(*course_id.split('/')))
        call_command('compute_grades', )
        self.asertEqual(offline_grade_calculation.call_count, 1)  # pylint: disable=no-member
        offline_grade_calculation.assert_called_with(CourseKey.from_string('MITx/0.0001/2016_Fall'))

    def test_compute_grades_command_multiple_courses(self):
        course_id1 = 'MITx/0.0001/2016_Fall'
        course_id2 = 'MITx/0.0002/2016_Fall'
        CourseKey.from_string = Mock()
        offline_grade_calculation = Mock()  # pylint: disable=redefined-outer-name
        call_command('compute_grades', '{0} {1}'.format(course_id1, course_id1))
        self.asertEqual(offline_grade_calculation.call_count, 2)  # pylint: disable=no-member
        CourseKey.from_string.assert_called_with(course_id1)
        CourseKey.from_string.assert_called_with(course_id2)
