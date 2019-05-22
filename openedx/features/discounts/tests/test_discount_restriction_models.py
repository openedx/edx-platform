"""
Test discount restriction config
"""
from __future__ import absolute_import

import itertools

import ddt

from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.features.discounts.models import DiscountRestrictionConfig
from student.tests.factories import UserFactory


@ddt.ddt
class TestDiscountRestrictionConfig(CacheIsolationTestCase):
    """
    Test discount restriction config
    """
    ENABLED_CACHES = ['default']

    def setUp(self):
        self.course_overview = CourseOverviewFactory.create()
        self.user = UserFactory.create()
        super(TestDiscountRestrictionConfig, self).setUp()

    @ddt.data(True, False)
    def test_enabled_for_course(
        self,
        enabled,
    ):
        DiscountRestrictionConfig.objects.create(
            enabled=enabled,
            course=self.course_overview,
        )
        course_key = self.course_overview.id

        self.assertEqual(
            enabled,
            DiscountRestrictionConfig.current(course_key=course_key).enabled
        )

    @ddt.data(
        # Generate all combinations of setting each configuration level to True/False/None
        *itertools.product(*[(True, False, None)] * 4)
    )
    @ddt.unpack
    def test_config_overrides(self, global_setting, site_setting, org_setting, course_setting):
        """
        Test that the stacked configuration overrides happen in the correct order and priority.

        This is tested by exhaustively setting each combination of contexts, and validating that only
        the lowest level context that is set to not-None is applied.
        """
        # Add a bunch of configuration outside the contexts that are being tested, to make sure
        # there are no leaks of configuration across contexts
        non_test_course_enabled = CourseOverviewFactory.create(org='non-test-org-enabled')
        non_test_course_disabled = CourseOverviewFactory.create(org='non-test-org-disabled')
        non_test_site_cfg_enabled = SiteConfigurationFactory.create(
            values={'course_org_filter': non_test_course_enabled.org}
        )
        non_test_site_cfg_disabled = SiteConfigurationFactory.create(
            values={'course_org_filter': non_test_course_disabled.org}
        )

        DiscountRestrictionConfig.objects.create(course=non_test_course_enabled, enabled=True)
        DiscountRestrictionConfig.objects.create(course=non_test_course_disabled, enabled=False)
        DiscountRestrictionConfig.objects.create(org=non_test_course_enabled.org, enabled=True)
        DiscountRestrictionConfig.objects.create(org=non_test_course_disabled.org, enabled=False)
        DiscountRestrictionConfig.objects.create(site=non_test_site_cfg_enabled.site, enabled=True)
        DiscountRestrictionConfig.objects.create(site=non_test_site_cfg_disabled.site, enabled=False)

        # Set up test objects
        test_course = CourseOverviewFactory.create(org='test-org')
        test_site_cfg = SiteConfigurationFactory.create(values={'course_org_filter': test_course.org})

        DiscountRestrictionConfig.objects.create(enabled=global_setting)
        DiscountRestrictionConfig.objects.create(course=test_course, enabled=course_setting)
        DiscountRestrictionConfig.objects.create(org=test_course.org, enabled=org_setting)
        DiscountRestrictionConfig.objects.create(site=test_site_cfg.site, enabled=site_setting)

        expected_global_setting = self._resolve_settings([global_setting])
        expected_site_setting = self._resolve_settings([global_setting, site_setting])
        expected_org_setting = self._resolve_settings([global_setting, site_setting, org_setting])
        expected_course_setting = self._resolve_settings([global_setting, site_setting, org_setting, course_setting])

        self.assertEqual(expected_global_setting, DiscountRestrictionConfig.current().enabled)
        self.assertEqual(expected_site_setting, DiscountRestrictionConfig.current(site=test_site_cfg.site).enabled)
        self.assertEqual(expected_org_setting, DiscountRestrictionConfig.current(org=test_course.org).enabled)
        self.assertEqual(expected_course_setting, DiscountRestrictionConfig.current(course_key=test_course.id).enabled)

    def _resolve_settings(self, settings):
        if all(setting is None for setting in settings):
            return None

        return [
            setting
            for setting
            in settings
            if setting is not None
        ][-1]
