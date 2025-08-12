"""
Tests of CourseDurationLimitConfig.
"""

import itertools
from datetime import datetime, timedelta
from unittest.mock import Mock

import ddt
import pytest
from openedx.core.lib.time_zone_utils import get_utc_timezone
from django.utils import timezone
from edx_django_utils.cache import RequestCache
from opaque_keys.edx.locator import CourseLocator

from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from openedx.core.djangoapps.config_model_utils.models import Provenance
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig


@ddt.ddt
class TestCourseDurationLimitConfig(CacheIsolationTestCase):
    """
    Tests of CourseDurationLimitConfig
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        self.course_overview = CourseOverviewFactory.create()
        CourseModeFactory.create(course_id=self.course_overview.id, mode_slug='audit')
        CourseModeFactory.create(course_id=self.course_overview.id, mode_slug='verified')
        self.user = UserFactory.create()
        super().setUp()  # lint-amnesty, pylint: disable=super-with-arguments

    @ddt.data(
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    )
    @ddt.unpack
    def test_enabled_for_enrollment(
        self,
        already_enrolled,
        enrolled_before_enabled,
    ):

        # Tweak the datetime to enable the config so that it is either before
        # or after now (which is when the enrollment will be created)
        if enrolled_before_enabled:
            enabled_as_of = timezone.now() + timedelta(days=1)
        else:
            enabled_as_of = timezone.now() - timedelta(days=1)

        CourseDurationLimitConfig.objects.create(
            enabled=True,
            course=self.course_overview,
            enabled_as_of=enabled_as_of,
        )

        if already_enrolled:
            existing_enrollment = CourseEnrollmentFactory.create(  # lint-amnesty, pylint: disable=unused-variable
                user=self.user,
                course=self.course_overview,
            )
        else:
            existing_enrollment = None

        user = self.user
        course_key = self.course_overview.id  # lint-amnesty, pylint: disable=unused-variable

        query_count = 7

        with self.assertNumQueries(query_count):
            enabled = CourseDurationLimitConfig.enabled_for_enrollment(user, self.course_overview)
            assert (not enrolled_before_enabled) == enabled

    def test_enabled_for_enrollment_failure(self):
        with pytest.raises(ValueError):
            CourseDurationLimitConfig.enabled_for_enrollment(None, None)
        with pytest.raises(ValueError):
            CourseDurationLimitConfig.enabled_for_enrollment(
                Mock(name='user'),
                None
            )
        with pytest.raises(ValueError):
            CourseDurationLimitConfig.enabled_for_enrollment(
                None,
                Mock(name='course_key')
            )

    @ddt.data(True, False)
    def test_enabled_for_course(
        self,
        before_enabled,
    ):
        config = CourseDurationLimitConfig.objects.create(
            enabled=True,
            course=self.course_overview,
            enabled_as_of=timezone.now(),
        )

        # Tweak the datetime to check for course enablement so it is either
        # before or after when the configuration was enabled
        if before_enabled:
            target_datetime = config.enabled_as_of - timedelta(days=1)
        else:
            target_datetime = config.enabled_as_of + timedelta(days=1)

        course_key = self.course_overview.id

        assert (not before_enabled) == CourseDurationLimitConfig.enabled_for_course(
            course_key=course_key, target_datetime=target_datetime
        )

    @ddt.data(
        # Generate all combinations of setting each configuration level to True/False/None
        *itertools.product(*([(True, False, None)] * 4 + [(True, False)]))
    )
    @ddt.unpack
    def test_config_overrides(self, global_setting, site_setting, org_setting, course_setting, reverse_order):
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
            site_values={'course_org_filter': non_test_course_enabled.org}
        )
        non_test_site_cfg_disabled = SiteConfigurationFactory.create(
            site_values={'course_org_filter': non_test_course_disabled.org}
        )

        CourseDurationLimitConfig.objects.create(course=non_test_course_enabled, enabled=True)
        CourseDurationLimitConfig.objects.create(course=non_test_course_disabled, enabled=False)
        CourseDurationLimitConfig.objects.create(org=non_test_course_enabled.org, enabled=True)
        CourseDurationLimitConfig.objects.create(org=non_test_course_disabled.org, enabled=False)
        CourseDurationLimitConfig.objects.create(site=non_test_site_cfg_enabled.site, enabled=True)
        CourseDurationLimitConfig.objects.create(site=non_test_site_cfg_disabled.site, enabled=False)

        # Set up test objects
        test_course = CourseOverviewFactory.create(org='test-org')
        test_site_cfg = SiteConfigurationFactory.create(
            site_values={'course_org_filter': test_course.org}
        )

        if reverse_order:
            CourseDurationLimitConfig.objects.create(site=test_site_cfg.site, enabled=site_setting)
            CourseDurationLimitConfig.objects.create(org=test_course.org, enabled=org_setting)
            CourseDurationLimitConfig.objects.create(course=test_course, enabled=course_setting)
            CourseDurationLimitConfig.objects.create(enabled=global_setting)
        else:
            CourseDurationLimitConfig.objects.create(enabled=global_setting)
            CourseDurationLimitConfig.objects.create(course=test_course, enabled=course_setting)
            CourseDurationLimitConfig.objects.create(org=test_course.org, enabled=org_setting)
            CourseDurationLimitConfig.objects.create(site=test_site_cfg.site, enabled=site_setting)

        expected_global_setting = self._resolve_settings([global_setting])
        expected_site_setting = self._resolve_settings([global_setting, site_setting])
        expected_org_setting = self._resolve_settings([global_setting, site_setting, org_setting])
        expected_course_setting = self._resolve_settings([global_setting, site_setting, org_setting, course_setting])

        assert expected_global_setting == CourseDurationLimitConfig.current().enabled
        assert expected_site_setting == CourseDurationLimitConfig.current(site=test_site_cfg.site).enabled
        assert expected_org_setting == CourseDurationLimitConfig.current(org=test_course.org).enabled
        assert expected_course_setting == CourseDurationLimitConfig.current(course_key=test_course.id).enabled

    def test_all_current_course_configs(self):
        # Set up test objects
        for global_setting in (True, False, None):
            CourseDurationLimitConfig.objects.create(enabled=global_setting, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))  # lint-amnesty, pylint: disable=line-too-long
            for site_setting in (True, False, None):
                test_site_cfg = SiteConfigurationFactory.create(
                    site_values={'course_org_filter': []}
                )
                CourseDurationLimitConfig.objects.create(
                    site=test_site_cfg.site, enabled=site_setting, enabled_as_of=datetime(
                        2018, 1, 1, tzinfo=get_utc_timezone())
                )

                for org_setting in (True, False, None):
                    test_org = f"{test_site_cfg.id}-{org_setting}"
                    test_site_cfg.site_values['course_org_filter'].append(test_org)
                    test_site_cfg.save()

                    CourseDurationLimitConfig.objects.create(
                        org=test_org, enabled=org_setting, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone())
                    )

                    for course_setting in (True, False, None):
                        test_course = CourseOverviewFactory.create(
                            org=test_org,
                            id=CourseLocator(test_org, 'test_course', f'run-{course_setting}')
                        )
                        CourseDurationLimitConfig.objects.create(
                            course=test_course, enabled=course_setting, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone())  # lint-amnesty, pylint: disable=line-too-long
                        )

            with self.assertNumQueries(4):
                all_configs = CourseDurationLimitConfig.all_current_course_configs()

        # Deliberatly using the last all_configs that was checked after the 3rd pass through the global_settings loop
        # We should be creating 3^4 courses (3 global values * 3 site values * 3 org values * 3 course values)
        # Plus 1 for the edX/toy/2012_Fall course
        assert len(all_configs) == ((3 ** 4) + 1)

        # Point-test some of the final configurations
        assert all_configs[CourseLocator('7-True', 'test_course', 'run-None')] == {
            'enabled': (True, Provenance.org),
            'enabled_as_of': (datetime(2018, 1, 1, 0, tzinfo=get_utc_timezone()),
                              Provenance.run)
        }
        assert all_configs[CourseLocator('7-True', 'test_course', 'run-False')] == {
            'enabled': (False, Provenance.run),
            'enabled_as_of': (datetime(2018, 1, 1, 0, tzinfo=get_utc_timezone()),
                              Provenance.run)
        }
        assert all_configs[CourseLocator('7-None', 'test_course', 'run-None')] == {
            'enabled': (True, Provenance.site),
            'enabled_as_of': (datetime(2018, 1, 1, 0, tzinfo=get_utc_timezone()),
                              Provenance.run)
        }

    def test_caching_global(self):
        global_config = CourseDurationLimitConfig(
            enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))
        global_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the global value is not retrieved from cache after save
        with self.assertNumQueries(1):
            assert CourseDurationLimitConfig.current().enabled

        RequestCache.clear_all_namespaces()

        # Check that the global value can be retrieved from cache after read
        with self.assertNumQueries(0):
            assert CourseDurationLimitConfig.current().enabled

        global_config.enabled = False
        global_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the global value in cache was deleted on save
        with self.assertNumQueries(1):
            assert not CourseDurationLimitConfig.current().enabled

    def test_caching_site(self):
        site_cfg = SiteConfigurationFactory()
        site_config = CourseDurationLimitConfig(site=site_cfg.site, enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))  # lint-amnesty, pylint: disable=line-too-long
        site_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the site value is not retrieved from cache after save
        with self.assertNumQueries(1):
            assert CourseDurationLimitConfig.current(site=site_cfg.site).enabled

        RequestCache.clear_all_namespaces()

        # Check that the site value can be retrieved from cache after read
        with self.assertNumQueries(0):
            assert CourseDurationLimitConfig.current(site=site_cfg.site).enabled

        site_config.enabled = False
        site_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the site value in cache was deleted on save
        with self.assertNumQueries(1):
            assert not CourseDurationLimitConfig.current(site=site_cfg.site).enabled

        global_config = CourseDurationLimitConfig(
            enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))
        global_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the site value is not updated in cache by changing the global value
        with self.assertNumQueries(0):
            assert not CourseDurationLimitConfig.current(site=site_cfg.site).enabled

    def test_caching_org(self):
        course = CourseOverviewFactory.create(org='test-org')
        site_cfg = SiteConfigurationFactory.create(
            site_values={'course_org_filter': course.org}
        )
        org_config = CourseDurationLimitConfig(org=course.org, enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))  # lint-amnesty, pylint: disable=line-too-long
        org_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the org value is not retrieved from cache after save
        with self.assertNumQueries(2):
            assert CourseDurationLimitConfig.current(org=course.org).enabled

        RequestCache.clear_all_namespaces()

        # Check that the org value can be retrieved from cache after read
        with self.assertNumQueries(0):
            assert CourseDurationLimitConfig.current(org=course.org).enabled

        org_config.enabled = False
        org_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the org value in cache was deleted on save
        with self.assertNumQueries(2):
            assert not CourseDurationLimitConfig.current(org=course.org).enabled

        global_config = CourseDurationLimitConfig(
            enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))
        global_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the org value is not updated in cache by changing the global value
        with self.assertNumQueries(0):
            assert not CourseDurationLimitConfig.current(org=course.org).enabled

        site_config = CourseDurationLimitConfig(site=site_cfg.site, enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))  # lint-amnesty, pylint: disable=line-too-long
        site_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the org value is not updated in cache by changing the site value
        with self.assertNumQueries(0):
            assert not CourseDurationLimitConfig.current(org=course.org).enabled

    def test_caching_course(self):
        course = CourseOverviewFactory.create(org='test-org')
        site_cfg = SiteConfigurationFactory.create(
            site_values={'course_org_filter': course.org}
        )
        course_config = CourseDurationLimitConfig(course=course, enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))  # lint-amnesty, pylint: disable=line-too-long
        course_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the org value is not retrieved from cache after save
        with self.assertNumQueries(2):
            assert CourseDurationLimitConfig.current(course_key=course.id).enabled

        RequestCache.clear_all_namespaces()

        # Check that the org value can be retrieved from cache after read
        with self.assertNumQueries(0):
            assert CourseDurationLimitConfig.current(course_key=course.id).enabled

        course_config.enabled = False
        course_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the org value in cache was deleted on save
        with self.assertNumQueries(2):
            assert not CourseDurationLimitConfig.current(course_key=course.id).enabled

        global_config = CourseDurationLimitConfig(
            enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))
        global_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the org value is not updated in cache by changing the global value
        with self.assertNumQueries(0):
            assert not CourseDurationLimitConfig.current(course_key=course.id).enabled

        site_config = CourseDurationLimitConfig(site=site_cfg.site, enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))  # lint-amnesty, pylint: disable=line-too-long
        site_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the org value is not updated in cache by changing the site value
        with self.assertNumQueries(0):
            assert not CourseDurationLimitConfig.current(course_key=course.id).enabled

        org_config = CourseDurationLimitConfig(org=course.org, enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=get_utc_timezone()))  # lint-amnesty, pylint: disable=line-too-long
        org_config.save()

        RequestCache.clear_all_namespaces()

        # Check that the org value is not updated in cache by changing the site value
        with self.assertNumQueries(0):
            assert not CourseDurationLimitConfig.current(course_key=course.id).enabled

    def _resolve_settings(self, settings):
        if all(setting is None for setting in settings):
            return None

        return [
            setting
            for setting
            in settings
            if setting is not None
        ][-1]
