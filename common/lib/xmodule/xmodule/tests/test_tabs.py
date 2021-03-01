"""
Tests for CourseTabsListTestCase.
"""
from unittest import TestCase
import ddt

from xmodule.tabs import CourseTabList, InvalidTabsException


@ddt.ddt
class CourseTabsListTestCase(TestCase):
    """
    Class containing CourseTabsListTestCase tests.
    """

    @ddt.data(
        [
            [],
            []
        ],
        [
            [
                {'type': 'courseware', 'course_staff_only': False, 'name': 'Courseware'},
                {'type': 'course_info', 'course_staff_only': False, 'name': 'Course Info'},
                {'type': 'discussion', 'course_staff_only': False, 'name': 'Discussion'},
                {'type': 'wiki', 'course_staff_only': False, 'name': 'Wiki'},
                {'type': 'textbooks', 'course_staff_only': False, 'name': 'Textbooks'},
                {'type': 'progress', 'course_staff_only': False, 'name': 'Progress'}
            ],
            [
                {'type': 'courseware', 'course_staff_only': False, 'name': 'Course'},
                {'type': 'discussion', 'course_staff_only': False, 'name': 'Discussion'},
                {'type': 'wiki', 'course_staff_only': False, 'name': 'Wiki'},
                {'type': 'textbooks', 'course_staff_only': False, 'name': 'Textbooks'},
                {'type': 'progress', 'course_staff_only': False, 'name': 'Progress'}
            ],
        ],
        [
            [
                {'type': 'course_info', 'course_staff_only': False, 'name': 'Home'},
                {'type': 'courseware', 'course_staff_only': False, 'name': 'Course'},
                {'type': 'discussion', 'course_staff_only': False, 'name': 'Discussion'},
                {'type': 'wiki', 'course_staff_only': False, 'name': 'Wiki'},
                {'type': 'textbooks', 'course_staff_only': False, 'name': 'Textbooks'},
                {'type': 'progress', 'course_staff_only': False, 'name': 'Progress'}
            ],
            [
                {'type': 'courseware', 'course_staff_only': False, 'name': 'Course'},
                {'type': 'discussion', 'course_staff_only': False, 'name': 'Discussion'},
                {'type': 'wiki', 'course_staff_only': False, 'name': 'Wiki'},
                {'type': 'textbooks', 'course_staff_only': False, 'name': 'Textbooks'},
                {'type': 'progress', 'course_staff_only': False, 'name': 'Progress'}
            ],
        ]
    )
    @ddt.unpack
    def test_upgrade_tabs(self, tabs, expected_result):
        """
        Tests that any existing `course_info` tab is properly removed
        """
        CourseTabList.upgrade_tabs(tabs)
        self.assertEqual(tabs, expected_result)

    @ddt.data(
        [
            [],
            True
        ],
        [
            [
                {'type': 'course_info', 'course_staff_only': False, 'name': 'Home'},
                {'type': 'courseware', 'course_staff_only': False, 'name': 'Course'},
                {'type': 'discussion', 'course_staff_only': False, 'name': 'Discussion'},
                {'type': 'wiki', 'course_staff_only': False, 'name': 'Wiki'},
                {'type': 'textbooks', 'course_staff_only': False, 'name': 'Textbooks'},
                {'type': 'progress', 'course_staff_only': False, 'name': 'Progress'}
            ],
            False
        ],
        [
            [
                {'type': 'courseware', 'course_staff_only': False, 'name': 'Course'},
                {'type': 'courseware', 'course_staff_only': False, 'name': 'Course'},
                {'type': 'discussion', 'course_staff_only': False, 'name': 'Discussion'},
                {'type': 'wiki', 'course_staff_only': False, 'name': 'Wiki'},
                {'type': 'textbooks', 'course_staff_only': False, 'name': 'Textbooks'},
                {'type': 'progress', 'course_staff_only': False, 'name': 'Progress'}
            ],
            False
        ],
        [
            [
                {'type': 'courseware', 'course_staff_only': False, 'name': 'Course'},
                {'type': 'discussion', 'course_staff_only': False, 'name': 'Discussion'},
                {'type': 'wiki', 'course_staff_only': False, 'name': 'Wiki'},
                {'type': 'textbooks', 'course_staff_only': False, 'name': 'Textbooks'},
                {'type': 'progress', 'course_staff_only': False, 'name': 'Progress'}
            ],
            True
        ]
    )
    @ddt.unpack
    def test_validate_tabs(self, tabs, expected_success):
        """
        Tests that invalid tab configurations properly raise `InvalidTabsException`

        Invalid tabs include duplicate tabs & the old `course_info` tab
        """
        if not expected_success:
            with self.assertRaises(InvalidTabsException):
                CourseTabList.validate_tabs(tabs)
        else:
            CourseTabList.validate_tabs(tabs)
