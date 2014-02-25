"""
Tests settings across configurations.
"""

import unittest

from django.conf import settings
from django.test import TestCase

_AUTH_FEATURES_KEY = 'ENABLE_THIRD_PARTY_AUTH'


class TestCommonSettings(TestCase):
    """Tests settings from lms/envs/common.py."""

    @unittest.skipUnless(_AUTH_FEATURES_KEY in settings.FEATURES, '%s not present' % _AUTH_FEATURES_KEY)
    def test_enable_third_party_auth_is_disabled(self):
        self.assertIs(False, settings.FEATURES.get(_AUTH_FEATURES_KEY))

    # TODO(johncox@google.com): happy path test when True.
