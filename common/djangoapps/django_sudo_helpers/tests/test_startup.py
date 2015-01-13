"""
Tests django-sudo startup
"""
import ddt

from django.conf import settings
from django.test import TestCase
from mock import patch

from django_sudo_helpers.startup import run


@ddt.ddt
class DjangoSudoStartupTestCase(TestCase):
    """
    Test django-sudo startup
    """
    @ddt.data(
        True,
        False,
    )
    def test_run_django_sudo(self, is_enabled):
        with patch.dict("django.conf.settings.FEATURES", {"ENABLE_DJANGO_SUDO": is_enabled}):
            self.assertEqual(settings.FEATURES["ENABLE_DJANGO_SUDO"], is_enabled)
            with patch('django_sudo_helpers.startup.enable_django_sudo') as mock_enable_django_sudo:
                run()
                self.assertEqual(mock_enable_django_sudo.called, is_enabled)
