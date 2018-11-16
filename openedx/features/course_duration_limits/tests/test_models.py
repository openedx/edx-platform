"""
Tests of CourseDurationLimitConfig.
"""

from datetime import timedelta, date
import itertools

import ddt
from mock import Mock

from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from openedx.features.course_duration_limits.config import CONTENT_TYPE_GATING_FLAG
from student.tests.factories import CourseEnrollmentFactory, UserFactory


@ddt.ddt
class TestCourseDurationLimitConfig(CacheIsolationTestCase):
    """
    Tests of CourseDurationLimitConfig
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        self.course_overview = CourseOverviewFactory.create()
        self.user = UserFactory.create()
        super(TestCourseDurationLimitConfig, self).setUp()

    @ddt.data(
        (True, True, True),
        (True, True, False),
        (True, False, True),
        (True, False, False),
        (False, False, True),
        (False, False, False),
    )
    @ddt.unpack
    def test_enabled_for_enrollment(
        self,
        already_enrolled,
        pass_enrollment,
        enrolled_before_enabled,
    ):

        # Tweak the day to enable the config so that it is either before
        # or after today (which is when the enrollment will be created)
        if enrolled_before_enabled:
            enabled_as_of = date.today() + timedelta(days=1)
        else:
            enabled_as_of = date.today() - timedelta(days=1)

        CourseDurationLimitConfig.objects.create(
            enabled=True,
            course=self.course_overview,
            enabled_as_of=enabled_as_of,
        )

        if already_enrolled:
            existing_enrollment = CourseEnrollmentFactory.create(
                user=self.user,
                course=self.course_overview,
            )
        else:
            existing_enrollment = None

        if pass_enrollment:
            enrollment = existing_enrollment
            user = None
            course_key = None
        else:
            enrollment = None
            user = self.user
            course_key = self.course_overview.id

        query_count = 5
        if not pass_enrollment and already_enrolled:
            query_count = 6

        with self.assertNumQueries(query_count):
            enabled = CourseDurationLimitConfig.enabled_for_enrollment(
                enrollment=enrollment,
                user=user,
                course_key=course_key,
            )
            self.assertEqual(not enrolled_before_enabled, enabled)

    def test_enabled_for_enrollment_failure(self):
        with self.assertRaises(ValueError):
            CourseDurationLimitConfig.enabled_for_enrollment(None, None, None)
        with self.assertRaises(ValueError):
            CourseDurationLimitConfig.enabled_for_enrollment(
                Mock(name='enrollment'),
                Mock(name='user'),
                None
            )
        with self.assertRaises(ValueError):
            CourseDurationLimitConfig.enabled_for_enrollment(
                Mock(name='enrollment'),
                None,
                Mock(name='course_key')
            )

    @override_waffle_flag(CONTENT_TYPE_GATING_FLAG, True)
    def test_enabled_for_enrollment_flag_override(self):
        self.assertTrue(CourseDurationLimitConfig.enabled_for_enrollment(
            None,
            None,
            None
        ))
        self.assertTrue(CourseDurationLimitConfig.enabled_for_enrollment(
            Mock(name='enrollment'),
            Mock(name='user'),
            None
        ))
        self.assertTrue(CourseDurationLimitConfig.enabled_for_enrollment(
            Mock(name='enrollment'),
            None,
            Mock(name='course_key')
        ))

    @ddt.data(True, False)
    def test_enabled_for_course(
        self,
        before_enabled,
    ):
        config = CourseDurationLimitConfig.objects.create(
            enabled=True,
            course=self.course_overview,
            enabled_as_of=date.today(),
        )

        # Tweak the day to check for course enablement so it is either
        # before or after when the configuration was enabled
        if before_enabled:
            target_date = config.enabled_as_of - timedelta(days=1)
        else:
            target_date = config.enabled_as_of + timedelta(days=1)

        course_key = self.course_overview.id

        self.assertEqual(
            not before_enabled,
            CourseDurationLimitConfig.enabled_for_course(
                course_key=course_key,
                target_date=target_date,
            )
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

        CourseDurationLimitConfig.objects.create(course=non_test_course_enabled, enabled=True)
        CourseDurationLimitConfig.objects.create(course=non_test_course_disabled, enabled=False)
        CourseDurationLimitConfig.objects.create(org=non_test_course_enabled.org, enabled=True)
        CourseDurationLimitConfig.objects.create(org=non_test_course_disabled.org, enabled=False)
        CourseDurationLimitConfig.objects.create(site=non_test_site_cfg_enabled.site, enabled=True)
        CourseDurationLimitConfig.objects.create(site=non_test_site_cfg_disabled.site, enabled=False)

        # Set up test objects
        test_course = CourseOverviewFactory.create(org='test-org')
        test_site_cfg = SiteConfigurationFactory.create(values={'course_org_filter': test_course.org})

        CourseDurationLimitConfig.objects.create(enabled=global_setting)
        CourseDurationLimitConfig.objects.create(course=test_course, enabled=course_setting)
        CourseDurationLimitConfig.objects.create(org=test_course.org, enabled=org_setting)
        CourseDurationLimitConfig.objects.create(site=test_site_cfg.site, enabled=site_setting)

        expected_global_setting = self._resolve_settings([global_setting])
        expected_site_setting = self._resolve_settings([global_setting, site_setting])
        expected_org_setting = self._resolve_settings([global_setting, site_setting, org_setting])
        expected_course_setting = self._resolve_settings([global_setting, site_setting, org_setting, course_setting])

        self.assertEqual(expected_global_setting, CourseDurationLimitConfig.current().enabled)
        self.assertEqual(expected_site_setting, CourseDurationLimitConfig.current(site=test_site_cfg.site).enabled)
        self.assertEqual(expected_org_setting, CourseDurationLimitConfig.current(org=test_course.org).enabled)
        self.assertEqual(expected_course_setting, CourseDurationLimitConfig.current(course_key=test_course.id).enabled)

    def test_caching_global(self):
        global_config = CourseDurationLimitConfig(enabled=True, enabled_as_of=date(2018, 1, 1))
        global_config.save()

        # Check that the global value is not retrieved from cache after save
        with self.assertNumQueries(1):
            self.assertTrue(CourseDurationLimitConfig.current().enabled)

        # Check that the global value can be retrieved from cache after read
        with self.assertNumQueries(0):
            self.assertTrue(CourseDurationLimitConfig.current().enabled)

        global_config.enabled = False
        global_config.save()

        # Check that the global value in cache was deleted on save
        with self.assertNumQueries(1):
            self.assertFalse(CourseDurationLimitConfig.current().enabled)

    def test_caching_site(self):
        site_cfg = SiteConfigurationFactory()
        site_config = CourseDurationLimitConfig(site=site_cfg.site, enabled=True, enabled_as_of=date(2018, 1, 1))
        site_config.save()

        # Check that the site value is not retrieved from cache after save
        with self.assertNumQueries(1):
            self.assertTrue(CourseDurationLimitConfig.current(site=site_cfg.site).enabled)

        # Check that the site value can be retrieved from cache after read
        with self.assertNumQueries(0):
            self.assertTrue(CourseDurationLimitConfig.current(site=site_cfg.site).enabled)

        site_config.enabled = False
        site_config.save()

        # Check that the site value in cache was deleted on save
        with self.assertNumQueries(1):
            self.assertFalse(CourseDurationLimitConfig.current(site=site_cfg.site).enabled)

        global_config = CourseDurationLimitConfig(enabled=True, enabled_as_of=date(2018, 1, 1))
        global_config.save()

        # Check that the site value is not updated in cache by changing the global value
        with self.assertNumQueries(0):
            self.assertFalse(CourseDurationLimitConfig.current(site=site_cfg.site).enabled)

    def test_caching_org(self):
        course = CourseOverviewFactory.create(org='test-org')
        site_cfg = SiteConfigurationFactory.create(values={'course_org_filter': course.org})
        org_config = CourseDurationLimitConfig(org=course.org, enabled=True, enabled_as_of=date(2018, 1, 1))
        org_config.save()

        # Check that the org value is not retrieved from cache after save
        with self.assertNumQueries(2):
            self.assertTrue(CourseDurationLimitConfig.current(org=course.org).enabled)

        # Check that the org value can be retrieved from cache after read
        with self.assertNumQueries(0):
            self.assertTrue(CourseDurationLimitConfig.current(org=course.org).enabled)

        org_config.enabled = False
        org_config.save()

        # Check that the org value in cache was deleted on save
        with self.assertNumQueries(2):
            self.assertFalse(CourseDurationLimitConfig.current(org=course.org).enabled)

        global_config = CourseDurationLimitConfig(enabled=True, enabled_as_of=date(2018, 1, 1))
        global_config.save()

        # Check that the org value is not updated in cache by changing the global value
        with self.assertNumQueries(0):
            self.assertFalse(CourseDurationLimitConfig.current(org=course.org).enabled)

        site_config = CourseDurationLimitConfig(site=site_cfg.site, enabled=True, enabled_as_of=date(2018, 1, 1))
        site_config.save()

        # Check that the org value is not updated in cache by changing the site value
        with self.assertNumQueries(0):
            self.assertFalse(CourseDurationLimitConfig.current(org=course.org).enabled)

    def test_caching_course(self):
        course = CourseOverviewFactory.create(org='test-org')
        site_cfg = SiteConfigurationFactory.create(values={'course_org_filter': course.org})
        course_config = CourseDurationLimitConfig(course=course, enabled=True, enabled_as_of=date(2018, 1, 1))
        course_config.save()

        # Check that the org value is not retrieved from cache after save
        with self.assertNumQueries(2):
            self.assertTrue(CourseDurationLimitConfig.current(course_key=course.id).enabled)

        # Check that the org value can be retrieved from cache after read
        with self.assertNumQueries(0):
            self.assertTrue(CourseDurationLimitConfig.current(course_key=course.id).enabled)

        course_config.enabled = False
        course_config.save()

        # Check that the org value in cache was deleted on save
        with self.assertNumQueries(2):
            self.assertFalse(CourseDurationLimitConfig.current(course_key=course.id).enabled)

        global_config = CourseDurationLimitConfig(enabled=True, enabled_as_of=date(2018, 1, 1))
        global_config.save()

        # Check that the org value is not updated in cache by changing the global value
        with self.assertNumQueries(0):
            self.assertFalse(CourseDurationLimitConfig.current(course_key=course.id).enabled)

        site_config = CourseDurationLimitConfig(site=site_cfg.site, enabled=True, enabled_as_of=date(2018, 1, 1))
        site_config.save()

        # Check that the org value is not updated in cache by changing the site value
        with self.assertNumQueries(0):
            self.assertFalse(CourseDurationLimitConfig.current(course_key=course.id).enabled)

        org_config = CourseDurationLimitConfig(org=course.org, enabled=True, enabled_as_of=date(2018, 1, 1))
        org_config.save()

        # Check that the org value is not updated in cache by changing the site value
        with self.assertNumQueries(0):
            self.assertFalse(CourseDurationLimitConfig.current(course_key=course.id).enabled)

    def _resolve_settings(self, settings):
        if all(setting is None for setting in settings):
            return None

        return [
            setting
            for setting
            in settings
            if setting is not None
        ][-1]
