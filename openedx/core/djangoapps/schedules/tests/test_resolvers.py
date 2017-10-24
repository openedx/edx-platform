import datetime
from unittest import skipUnless

import ddt
from django.conf import settings
from mock import patch, DEFAULT, Mock

from openedx.core.djangoapps.schedules.resolvers import BinnedSchedulesBaseResolver
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory, SiteConfigurationFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestBinnedSchedulesBaseResolver(CacheIsolationTestCase):
    def setUp(self):
        super(TestBinnedSchedulesBaseResolver, self).setUp()

        self.site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory(site=self.site)
        self.schedule_config = ScheduleConfigFactory.create(site=self.site)
        self.resolver = BinnedSchedulesBaseResolver(
            async_send_task=Mock(name='async_send_task'),
            site=self.site,
            target_datetime=datetime.datetime.now(),
            day_offset=3,
            bin_num=2,
        )

    @ddt.unpack
    @ddt.data(
        ('course1', ['course1']),
        (['course1', 'course2'], ['course1', 'course2'])
    )
    def test_get_course_org_filter_include(self, course_org_filter, expected_org_list):
        self.site_config.values['course_org_filter'] = course_org_filter
        self.site_config.save()
        exclude_orgs, org_list = self.resolver.get_course_org_filter()
        assert not exclude_orgs
        assert org_list == expected_org_list

    @ddt.unpack
    @ddt.data(
        (None, []),
        ('course1', [u'course1']),
        (['course1', 'course2'], [u'course1', u'course2'])
    )
    def test_get_course_org_filter_exclude(self, course_org_filter, expected_org_list):
        SiteConfigurationFactory.create(
            values={'course_org_filter': course_org_filter},
        )
        exclude_orgs, org_list = self.resolver.get_course_org_filter()
        assert exclude_orgs
        self.assertItemsEqual(org_list, expected_org_list)
