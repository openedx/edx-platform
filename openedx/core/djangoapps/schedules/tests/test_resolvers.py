"""
Tests for schedules resolvers
"""


import datetime
from unittest.mock import Mock, patch

import ddt
from django.test import TestCase
from django.test.utils import override_settings
from testfixtures import LogCapture
from waffle.testutils import override_switch

from edx_toggles.toggles.testutils import override_waffle_flag
from openedx.core.djangoapps.schedules.config import COURSE_UPDATE_WAFFLE_FLAG
from openedx.core.djangoapps.schedules.models import Schedule
from openedx.core.djangoapps.schedules.resolvers import (
    LOG,
    BinnedSchedulesBaseResolver,
    CourseNextSectionUpdate,
    CourseUpdateResolver
)
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangolib.testing.utils import CacheIsolationMixin, skip_unless_lms
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class SchedulesResolverTestMixin(CacheIsolationMixin):
    """
    Base class for the resolver tests.
    """
    def setUp(self):
        super().setUp()
        self.site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory(site=self.site)
        self.schedule_config = ScheduleConfigFactory.create(site=self.site)


@ddt.ddt
@skip_unless_lms
class TestBinnedSchedulesBaseResolver(SchedulesResolverTestMixin, TestCase):
    """
    Tests the BinnedSchedulesBaseResolver.
    """
    def setUp(self):
        super().setUp()

        self.resolver = BinnedSchedulesBaseResolver(
            async_send_task=Mock(name='async_send_task'),
            site=self.site,
            target_datetime=datetime.datetime.now(),
            day_offset=3,
            bin_num=2,
        )

    @ddt.data(
        'course1'
    )
    def test_get_course_org_filter_equal(self, course_org_filter):
        self.site_config.site_values['course_org_filter'] = course_org_filter
        self.site_config.save()
        mock_query = Mock()
        result = self.resolver.filter_by_org(mock_query)
        self.assertEqual(result, mock_query.filter.return_value)
        mock_query.filter.assert_called_once_with(enrollment__course__org=course_org_filter)

    @ddt.unpack
    @ddt.data(
        (['course1', 'course2'], ['course1', 'course2'])
    )
    def test_get_course_org_filter_include__in(self, course_org_filter, expected_org_list):
        self.site_config.site_values['course_org_filter'] = course_org_filter
        self.site_config.save()
        mock_query = Mock()
        result = self.resolver.filter_by_org(mock_query)
        self.assertEqual(result, mock_query.filter.return_value)
        mock_query.filter.assert_called_once_with(enrollment__course__org__in=expected_org_list)

    @ddt.unpack
    @ddt.data(
        (None, set([])),
        ('course1', set(['course1'])),
        (['course1', 'course2'], set(['course1', 'course2']))
    )
    def test_get_course_org_filter_exclude__in(self, course_org_filter, expected_org_list):
        SiteConfigurationFactory.create(
            site_values={'course_org_filter': course_org_filter}
        )
        mock_query = Mock()
        result = self.resolver.filter_by_org(mock_query)
        mock_query.exclude.assert_called_once_with(enrollment__course__org__in=expected_org_list)
        self.assertEqual(result, mock_query.exclude.return_value)


@skip_unless_lms
class TestCourseUpdateResolver(SchedulesResolverTestMixin, ModuleStoreTestCase):
    """
    Tests the CourseUpdateResolver.
    """
    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(highlights_enabled_for_messaging=True, self_paced=True)
        with self.store.bulk_operations(self.course.id):
            ItemFactory.create(parent=self.course, category='chapter', highlights=['good stuff'])

    def create_resolver(self):
        """
        Creates a CourseUpdateResolver with an enrollment to schedule.
        """
        with patch('openedx.core.djangoapps.schedules.signals.get_current_site') as mock_get_current_site:
            mock_get_current_site.return_value = self.site_config.site
            enrollment = CourseEnrollmentFactory(course_id=self.course.id, user=self.user, mode='audit')

        return CourseUpdateResolver(
            async_send_task=Mock(name='async_send_task'),
            site=self.site_config.site,
            target_datetime=enrollment.schedule.start_date,
            day_offset=-7,
            bin_num=CourseUpdateResolver.bin_num_for_user_id(self.user.id),
        )

    @override_settings(CONTACT_MAILING_ADDRESS='123 Sesame Street')
    @override_settings(LOGO_URL_PNG='https://www.logo.png')
    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_schedule_context(self):
        resolver = self.create_resolver()
        schedules = list(resolver.schedules_for_bin())
        expected_context = {
            'contact_email': 'info@example.com',
            'contact_mailing_address': '123 Sesame Street',
            'course_ids': [str(self.course.id)],
            'course_name': self.course.display_name,
            'course_url': '/courses/{}/course/'.format(self.course.id),
            'dashboard_url': '/dashboard',
            'homepage_url': '/',
            'mobile_store_urls': {},
            'logo_url': 'https://www.logo.png',
            'platform_name': '\xe9dX',
            'show_upsell': False,
            'social_media_urls': {},
            'template_revision': 'release',
            'unsubscribe_url': None,
            'week_highlights': ['good stuff'],
            'week_num': 1,
        }
        self.assertEqual(schedules, [(self.user, None, expected_context, True)])

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    @override_switch('schedules.course_update_show_unsubscribe', True)
    def test_schedule_context_show_unsubscribe(self):
        resolver = self.create_resolver()
        schedules = list(resolver.schedules_for_bin())
        self.assertIn('optout', schedules[0][2]['unsubscribe_url'])

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_get_schedules_with_target_date_by_bin_and_orgs_filter_inactive_users(self):
        """Tests that schedules of inactive users are excluded"""
        resolver = self.create_resolver()
        schedules = resolver.get_schedules_with_target_date_by_bin_and_orgs()

        self.assertEqual(schedules.count(), 1)
        self.user.is_active = False
        self.user.save()
        schedules = resolver.get_schedules_with_target_date_by_bin_and_orgs()
        self.assertEqual(schedules.count(), 0)


@skip_unless_lms
class TestCourseNextSectionUpdateResolver(SchedulesResolverTestMixin, ModuleStoreTestCase):
    """
    Tests the TestCourseNextSectionUpdateResolver.
    """
    def setUp(self):
        super().setUp()
        self.today = datetime.datetime.utcnow()
        self.yesterday = self.today - datetime.timedelta(days=1)
        self.course = CourseFactory.create(
            highlights_enabled_for_messaging=True, self_paced=True,
            # putting it in the past so the schedule can be later than the start
            start=self.today - datetime.timedelta(days=30)
        )

        with self.store.bulk_operations(self.course.id):
            ItemFactory.create(parent=self.course, category='chapter', highlights=['good stuff 1'])
            ItemFactory.create(parent=self.course, category='chapter', highlights=['good stuff 2'])
            ItemFactory.create(parent=self.course, category='chapter', highlights=['good stuff 3'])
            ItemFactory.create(parent=self.course, category='chapter', highlights=['good stuff 4'])

    def create_resolver(self, user_start_date_offset=8):
        """
        Creates a CourseNextSectionUpdateResolver with an enrollment to schedule.
        """
        with patch('openedx.core.djangoapps.schedules.signals.get_current_site') as mock_get_current_site:
            mock_get_current_site.return_value = self.site_config.site
            CourseEnrollmentFactory(course_id=self.course.id, user=self.user, mode='audit')

        # Need to update the user's schedule so the due date for the chapter we want
        # matches with the user's schedule and the target date. The numbers are based on the
        # course having the default course duration of 28 days.
        user_schedule = Schedule.objects.first()
        user_schedule.start_date = self.today - datetime.timedelta(days=user_start_date_offset)
        user_schedule.save()

        return CourseNextSectionUpdate(
            async_send_task=Mock(name='async_send_task'),
            site=self.site_config.site,
            target_datetime=self.yesterday,
            course_id=self.course.id,
        )

    @override_settings(CONTACT_MAILING_ADDRESS='123 Sesame Street')
    @override_settings(LOGO_URL_PNG='https://www.logo.png')
    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_schedule_context(self):
        resolver = self.create_resolver()
        # using this to make sure the select_related stays intact
        with self.assertNumQueries(17):
            sc = resolver.get_schedules()
            schedules = list(sc)

        expected_context = {
            'contact_email': 'info@example.com',
            'contact_mailing_address': '123 Sesame Street',
            'course_ids': [str(self.course.id)],
            'course_name': self.course.display_name,
            'course_url': '/courses/{}/course/'.format(self.course.id),
            'dashboard_url': '/dashboard',
            'homepage_url': '/',
            'mobile_store_urls': {},
            'logo_url': 'https://www.logo.png',
            'platform_name': '\xe9dX',
            'show_upsell': False,
            'social_media_urls': {},
            'template_revision': 'release',
            'unsubscribe_url': None,
            'week_highlights': ['good stuff 2'],
            'week_num': 2,
        }
        self.assertEqual(schedules, [(self.user, None, expected_context, True)])

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    @override_switch('schedules.course_update_show_unsubscribe', True)
    def test_schedule_context_show_unsubscribe(self):
        resolver = self.create_resolver()
        schedules = list(resolver.get_schedules())
        self.assertIn('optout', schedules[0][2]['unsubscribe_url'])

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_schedule_context_error(self):
        resolver = self.create_resolver(user_start_date_offset=29)
        with LogCapture(LOG.name) as log_capture:
            list(resolver.get_schedules())
            log_message = ('Next Section Course Update: Last section was reached. '
                           'There are no more highlights for {}'.format(self.course.id))
            log_capture.check_present((LOG.name, 'WARNING', log_message))

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_no_updates_if_course_ended(self):
        self.course.end = self.yesterday
        self.course = self.update_course(self.course, self.user.id)
        resolver = self.create_resolver()
        schedules = list(resolver.get_schedules())
        self.assertListEqual(schedules, [])
