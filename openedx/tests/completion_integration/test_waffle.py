"""
Tests waffle mechanics and feature-gating for block completion features.
"""

from __future__ import absolute_import, unicode_literals

from completion import waffle
import ddt
from django.test import TestCase
import mock
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory, SiteConfigurationFactory
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
@ddt.ddt
class FeatureGatingTests(TestCase):
    """
    Tests the logic of the completion feature-gating functions in the LMS.
    """
    def setUp(self):
        self.site = SiteFactory.create()
        self.site_patcher = mock.patch('completion.waffle.get_current_site')
        mocked_current_site = self.site_patcher.start()
        mocked_current_site.return_value = self.site

        self.course_key = CourseKey.from_string('course-v1:edX+DemoX+Demo_Course')

    def tearDown(self):
        self.site_patcher.stop()

    def _make_site_config(self, enable_feature):
        site_config = SiteConfigurationFactory.create(site=self.site)
        site_config.values[waffle.ENABLE_SITE_VISUAL_PROGRESS] = enable_feature
        site_config.save()

    def test_site_disables_visual_progress_no_config(self):
        assert waffle.site_disables_visual_progress() is False

    @ddt.data(True, False)
    def test_site_disables_visual_progress_with_config(self, config_value):
        self._make_site_config(config_value)
        assert (not config_value) == waffle.site_disables_visual_progress()

    def test_visual_progress_gating_tracking_disabled(self):
        with waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, False):
            assert waffle.visual_progress_enabled(self.course_key) is False

    def test_visual_progress_gating_site_disabled(self):
        self._make_site_config(False)
        assert waffle.visual_progress_enabled(self.course_key) is False

    def test_visual_progress_gating_course_disabled(self):
        self._make_site_config(True)
        with waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, True):
            with waffle.waffle().override(waffle.ENABLE_VISUAL_PROGRESS, False):
                with override_waffle_flag(waffle.waffle_flag(), active=False):
                    assert waffle.visual_progress_enabled(self.course_key) is False

    def test_visual_progress_happy_path_no_site_config(self):
        with waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, True):
            with waffle.waffle().override(waffle.ENABLE_VISUAL_PROGRESS, True):
                assert waffle.visual_progress_enabled(self.course_key) is True

    def test_visual_progress_happy_path_with_site_config(self):
        self._make_site_config(True)
        with waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, True):
            with waffle.waffle().override(waffle.ENABLE_VISUAL_PROGRESS, True):
                assert waffle.visual_progress_enabled(self.course_key) is True

    def test_visual_progress_happy_path_visual_switch_disabled(self):
        self._make_site_config(True)
        with waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, True):
            with waffle.waffle().override(waffle.ENABLE_VISUAL_PROGRESS, False):
                with override_waffle_flag(waffle.waffle_flag(), active=True):
                    assert waffle.visual_progress_enabled(self.course_key) is True
