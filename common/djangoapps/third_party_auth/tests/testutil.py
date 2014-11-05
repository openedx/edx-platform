"""
Utilities for writing third_party_auth tests.

Used by Django and non-Django tests; must not have Django deps.
"""

import unittest

from third_party_auth import provider


AUTH_FEATURES_KEY = 'ENABLE_THIRD_PARTY_AUTH'


class FakeDjangoSettings(object):
    """A fake for Django settings."""

    def __init__(self, mappings):
        """Initializes the fake from mappings dict."""
        for key, value in mappings.iteritems():
            setattr(self, key, value)


class TestCase(unittest.TestCase):
    """Base class for auth test cases."""

    # Allow access to protected methods (or module-protected methods) under
    # test.
    # pylint: disable-msg=protected-access

    def setUp(self):
        super(TestCase, self).setUp()
        self._original_providers = provider.Registry._get_all()
        provider.Registry._reset()

    def tearDown(self):
        provider.Registry._reset()
        provider.Registry.configure_once(self._original_providers)
        super(TestCase, self).tearDown()
