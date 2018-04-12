"""Unit tests for third_party_auth/pipeline.py."""

import random
import unittest

from third_party_auth import pipeline
from third_party_auth.tests import testutil


# Allow tests access to protected methods (or module-protected methods) under test.
# pylint: disable=protected-access


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
class ProviderUserStateTestCase(testutil.TestCase):
    """Tests ProviderUserState behavior."""

    def test_get_unlink_form_name(self):
        google_provider = self.configure_google_provider(enabled=True)
        state = pipeline.ProviderUserState(google_provider, object(), None)
        self.assertEqual(google_provider.provider_id + '_unlink_form', state.get_unlink_form_name())
