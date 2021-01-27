"""
Tests for LTI Course tabs.
"""
from unittest.mock import Mock, patch

from lms.djangoapps.courseware.tests.test_tabs import TabTestCase
from openedx.features.lti_course_tab.tab import DiscussionLtiCourseTab


class DiscussionLtiCourseTabTestCase(TabTestCase):
    """Test cases for LTI Discussion Tab."""

    def check_discussion_tab(self):
        """Helper function for verifying the LTI discussion tab."""
        return self.check_tab(
            tab_class=DiscussionLtiCourseTab,
            dict_tab={'type': DiscussionLtiCourseTab.type, 'name': 'same'},
            expected_link=self.reverse('course_tab_view', args=[str(self.course.id), DiscussionLtiCourseTab.type]),
            expected_tab_id=DiscussionLtiCourseTab.type,
            invalid_dict_tab=None,
        )

    @patch('openedx.features.lti_course_tab.tab.DiscussionsConfiguration.get')
    @patch('common.djangoapps.student.models.CourseEnrollment.is_enrolled')
    def test_discussion_lti_tab(self, is_enrolled, discussion_config_get):
        is_enrolled.return_value = True
        mock_config = Mock()
        mock_config.lti_configuration = {}
        mock_config.enabled = False
        discussion_config_get.return_value = mock_config
        tab = self.check_discussion_tab()
        self.check_can_display_results(
            tab, for_staff_only=True, for_enrolled_users_only=True, expected_value=False
        )
        mock_config.enabled = True
        self.check_discussion_tab()
        self.check_can_display_results(
            tab, for_staff_only=True, for_enrolled_users_only=True
        )
