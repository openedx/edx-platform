from courseware.models import DynamicUpgradeDeadlineConfiguration
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, FilteredQueryCountMixin
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory


class ScheduleBaseEmailTestBase(FilteredQueryCountMixin, CacheIsolationTestCase):

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(ScheduleBaseEmailTestBase, self).setUp()

        site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory.create(site=site)
        ScheduleConfigFactory.create(site=self.site_config.site)

        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
