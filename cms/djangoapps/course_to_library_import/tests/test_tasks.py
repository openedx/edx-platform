"""
Tests for tasks in course_to_library_import app.
"""

from unittest.mock import patch

from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from cms.djangoapps.course_to_library_import.tasks import save_courses_to_staged_content_task
from common.djangoapps.student.tests.factories import UserFactory


class TestSaveCourseSectionsToStagedContentTask(TestCase):
    """
    Test cases for save_course_sections_to_staged_content_task.
    """

    @patch('cms.djangoapps.course_to_library_import.tasks.modulestore')
    @patch('openedx.core.djangoapps.content_staging.api.stage_xblock_temporarily')
    def test_save_courses_to_staged_content_task(self, mock_stage_xblock_temporarily, mock_modulestore):

        course_ids = ('course-v1:edX+DemoX+Demo_Course', 'course-v1:edX+DemoX+Demo_Course2')
        user_id = UserFactory().id
        purpose = 'test_purpose'
        version_num = 1

        mock_course_keys = [CourseKey.from_string(course_id) for course_id in course_ids]
        mock_modulestore().get_items.return_value = sections = ['section1', 'section2']

        save_courses_to_staged_content_task(course_ids, user_id, purpose, version_num)

        for mock_course_key in mock_course_keys:
            mock_modulestore().get_items.assert_any_call(mock_course_key, qualifiers={"category": "chapter"})

        self.assertEqual(mock_stage_xblock_temporarily.call_count, len(sections) * len(course_ids))
        for section in sections:
            mock_stage_xblock_temporarily.assert_any_call(section, user_id, purpose=purpose, version_num=version_num)
