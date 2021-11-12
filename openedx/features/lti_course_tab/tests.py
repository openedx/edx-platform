"""
Tests for LTI Course tabs.
"""
import itertools
from unittest.mock import Mock, patch

import ddt
from django.test import RequestFactory
from lti_consumer.models import CourseAllowPIISharingInLTIFlag, LtiConfiguration

from lms.djangoapps.courseware.tests.test_tabs import TabTestCase
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration
from openedx.features.lti_course_tab.tab import DiscussionLtiCourseTab


@ddt.ddt
class DiscussionLtiCourseTabTestCase(TabTestCase):
    """Test cases for LTI Discussion Tab."""

    def setUp(self):
        super().setUp()
        self.discussion_config = DiscussionsConfiguration.objects.create(
            context_key=self.course.id,
            enabled=False,
            # Pick a provider that supports LTI
            provider_type="yellowdig",
        )
        self.discussion_config.lti_configuration = LtiConfiguration.objects.create(
            config_store=LtiConfiguration.CONFIG_ON_DB,
            lti_1p1_launch_url='http://test.url',
            lti_1p1_client_key='test_client_key',
            lti_1p1_client_secret='test_client_secret',
        )
        self.discussion_config.save()
        self.url = self.reverse('course_tab_view', args=[str(self.course.id), DiscussionLtiCourseTab.type])

    def check_discussion_tab(self):
        """Helper function for verifying the LTI discussion tab."""
        return self.check_tab(
            tab_class=DiscussionLtiCourseTab,
            dict_tab={'type': DiscussionLtiCourseTab.type, 'name': 'same'},
            expected_link=self.url,
            expected_tab_id=DiscussionLtiCourseTab.type,
            invalid_dict_tab=None,
        )

    @ddt.data(True, False)
    @patch('common.djangoapps.student.models.CourseEnrollment.is_enrolled', Mock(return_value=True))
    def test_pii_params_on_discussion_lti_tab(self, discussion_config_enabled):
        self.discussion_config.enabled = discussion_config_enabled
        self.discussion_config.save()
        tab = self.check_discussion_tab()
        self.check_can_display_results(
            tab,
            for_staff_only=True,
            for_enrolled_users_only=True,
            expected_value=discussion_config_enabled,
        )

    @ddt.data(*itertools.product((True, False), repeat=3))
    @ddt.unpack
    def test_discussion_lti_tab_pii(self, enable_sending_pii, share_username, share_email):
        CourseAllowPIISharingInLTIFlag.objects.create(course_id=self.course.id, enabled=enable_sending_pii)
        self.discussion_config.lti_configuration.lti_config = {
            "pii_share_username": share_username,
            "pii_share_email": share_email,
        }
        self.discussion_config.lti_configuration.save()
        tab = self.check_discussion_tab()
        request = RequestFactory().get(self.url)
        user = self.create_mock_user(is_enrolled=True)
        request.user = user
        embed_code = tab._get_lti_embed_code(self.course, request)  # pylint: disable=protected-access
        if enable_sending_pii and share_username:
            assert user.username in embed_code
        else:
            assert user.username not in embed_code
        if enable_sending_pii and share_email:
            assert user.email in embed_code
        else:
            assert user.email not in embed_code
