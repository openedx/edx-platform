import datetime
from unittest import skipUnless

import ddt
import pytz
from django.conf import settings
from mock import patch

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestSendEmailBaseCommand(CacheIsolationTestCase):
    def setUp(self):
        self.command = SendEmailBaseCommand()

    def test_init_resolver_class(self):
        assert self.command.resolver_class is None

    def test_make_resolver(self):
        with patch.object(self.command, 'resolver_class') as resolver_class:
            example_site = SiteFactory(domain='example.com')
            self.command.make_resolver(site_domain_name='example.com', date='2017-09-29')
            resolver_class.assert_called_once_with(
                example_site,
                datetime.datetime(2017, 9, 29, tzinfo=pytz.UTC)
            )

    def test_handle(self):
        with patch.object(self.command, 'make_resolver') as make_resolver:
            make_resolver.return_value = 'resolver'
            with patch.object(self.command, 'send_emails') as send_emails:
                self.command.handle(date='2017-09-29')
                make_resolver.assert_called_once_with(date='2017-09-29')
                send_emails.assert_called_once_with('resolver', date='2017-09-29')
