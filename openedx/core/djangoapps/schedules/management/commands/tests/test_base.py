import datetime
from unittest import skipUnless

import ddt
import pytz
from django.conf import settings
from mock import patch

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory, SiteConfigurationFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestSendEmailBaseCommand(CacheIsolationTestCase):
    def setUp(self):
        self.command = SendEmailBaseCommand()
        self.site = SiteFactory()
        self.site_config = SiteConfigurationFactory.create(site=self.site)

    def test_handle(self):
        with patch.object(self.command, 'send_emails') as send_emails:
            self.command.handle(site_domain_name=self.site.domain, date='2017-09-29')
            send_emails.assert_called_once_with(
                self.site,
                datetime.datetime(2017, 9, 29, tzinfo=pytz.UTC),
                None
            )
