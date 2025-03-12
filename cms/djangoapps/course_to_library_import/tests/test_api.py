"""
Test cases for course_to_library_import.api module.
"""

from unittest.mock import patch

import pytest

from cms.djangoapps.course_to_library_import.api import (
    save_courses_to_staged_content,
    COURSE_TO_LIBRARY_IMPORT_PURPOSE
)


@pytest.mark.parametrize("purpose, expected_purpose", [
    ('custom_purpose', 'custom_purpose'),
    (None, COURSE_TO_LIBRARY_IMPORT_PURPOSE),
])
@patch('cms.djangoapps.course_to_library_import.api.save_courses_to_staged_content_task')
def test_save_courses_to_staged_content(mock_task, purpose, expected_purpose):
    """
    Test save_course_to_staged_content function.

    Case 1: Purpose is provided.
    Case 2: Purpose is not provided
    """

    course_ids = ('course-v1:edX+DemoX+Demo_Course', 'course-v1:edX+DemoX+Demo_Course2')
    user_id = 1
    version_num = 1

    if purpose:
        save_courses_to_staged_content(course_ids, user_id, purpose, version_num)
    else:
        save_courses_to_staged_content(course_ids, user_id, version_num=version_num)

    mock_task.delay.assert_called_once_with(course_ids, user_id, expected_purpose, version_num)
