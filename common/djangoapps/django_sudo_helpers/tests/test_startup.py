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
    def test_run_third_party_auth(self, is_enabled):
        with patch.dict("django.conf.settings.FEATURES", {"ENABLE_THIRD_PARTY_AUTH": is_enabled}):
            self.assertEqual(settings.FEATURES["ENABLE_THIRD_PARTY_AUTH"], is_enabled)
            with patch('django_sudo_helpers.startup.enable_third_party_auth_for_sudo') as mock_third_party_for_sudo:
                run()
                if is_enabled:
                    self.assertTrue(mock_third_party_for_sudo.called)
                else:
                    self.assertFalse(mock_third_party_for_sudo.called)
