"""
Tests for  course live tab.
"""
import itertools
from unittest.mock import Mock, patch

import ddt
from django.test import RequestFactory
from edx_toggles.toggles.testutils import override_waffle_flag
from lti_consumer.models import CourseAllowPIISharingInLTIFlag, LtiConfiguration

from lms.djangoapps.courseware.tests.test_tabs import TabTestCase
from openedx.core.djangoapps.course_live.config.waffle import ENABLE_COURSE_LIVE
from openedx.core.djangoapps.course_live.models import CourseLiveConfiguration
from openedx.core.djangoapps.course_live.tab import CourseLiveTab


@ddt.ddt
class CourseLiveTabTestCase(TabTestCase):
    """Test cases for LTI CourseLive Tab."""

    def setUp(self):
        super().setUp()
        self.course_live_config = CourseLiveConfiguration.objects.create(
            course_key=self.course.id,
            enabled=False,
            provider_type="zoom",
        )
        self.course_live_config.lti_configuration = LtiConfiguration.objects.create(
            config_store=LtiConfiguration.CONFIG_ON_DB,
            lti_1p1_launch_url='http://test.url',
            lti_1p1_client_key='test_client_key',
            lti_1p1_client_secret='test_client_secret',
        )
        self.course_live_config.save()
        self.url = f"http://learning-mfe/course/{str(self.course.id)}/live"

    def check_course_live_tab(self):
        """
        Helper function for verifying the LTI course live tab.
        """
        return self.check_tab(
            tab_class=CourseLiveTab,
            dict_tab={'type': CourseLiveTab.type, 'name': 'same'},
            expected_link=self.url,
            expected_tab_id=CourseLiveTab.type,
            invalid_dict_tab=None,
        )

    @ddt.data(True, False)
    @patch('common.djangoapps.student.models.course_enrollment.CourseEnrollment.is_enrolled', Mock(return_value=True))
    def test_user_can_access_course_live_tab(self, course_live_config_enabled):
        """
        Test if tab is accessible to users with different roles
        """
        self.course_live_config.enabled = course_live_config_enabled
        self.course_live_config.save()
        tab = self.check_course_live_tab()
        with override_waffle_flag(ENABLE_COURSE_LIVE, True):
            self.check_can_display_results(
                tab,
                for_staff_only=True,
                for_enrolled_users_only=True,
                expected_value=course_live_config_enabled,
            )

    @ddt.data(*itertools.product((True, False), repeat=3))
    @ddt.unpack
    def test_course_live_lti_tab_pii(self, enable_sending_pii, share_username, share_email):
        """
        Test course Live is sharing pii data as expected
        """
        CourseAllowPIISharingInLTIFlag.objects.create(course_id=self.course.id, enabled=enable_sending_pii)
        self.course_live_config.lti_configuration.lti_config = {
            "pii_share_username": share_username,
            "pii_share_email": share_email,
        }
        self.course_live_config.lti_configuration.save()
        tab = self.check_course_live_tab()
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
