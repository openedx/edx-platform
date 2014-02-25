"""
Test configuration of providers.
"""

import unittest

from auth import provider


class RegistryTest(unittest.TestCase):
    """Tests registry discovery."""

    def setUp(self):
        super(RegistryTest, self).setUp()
        provider.Registry._reset()

    def test_calling_configure_once_twice_raises_value_error(self):
        provider.Registry.configure_once([provider.GoogleOauth2.NAME])

        with self.assertRaises(ValueError) as e:
            provider.Registry.configure_once([provider.GoogleOauth2.NAME])

        self.assertIn('already configured', e.exception.message)

    def test_configure_once_adds_gettable_providers(self):
        self.assertIsNone(provider.Registry.get(provider.GoogleOauth2.NAME))
        provider.Registry.configure_once([provider.GoogleOauth2.NAME])
        self.assertIs(provider.GoogleOauth2, provider.Registry.get(provider.GoogleOauth2.NAME))

    def test_configuring_provider_with_no_implementation_raises_value_error(self):
        with self.assertRaises(ValueError) as e:
            provider.Registry.configure_once(['no_implementation'])

        self.assertIn('no_implementation', e.exception.message)

    def test_configuring_single_provider_twice_raises_value_error(self):
        provider.Registry._enable(provider.GoogleOauth2)

        with self.assertRaises(ValueError) as e:
            provider.Registry.configure_once([provider.GoogleOauth2.NAME])

        self.assertIn('already enabled', e.exception.message)

    def test_enabled_returns_list_of_enabled_providers_sorted_by_name(self):
        provider.Registry.configure_once(provider.Registry._ALL.keys())
        self.assertEqual(
            sorted(provider.Registry._ALL.values(), key=lambda provider: provider.NAME), provider.Registry.enabled())

    def test_get_returns_enabled_provider(self):
        provider.Registry.configure_once([provider.GoogleOauth2.NAME])
        self.assertIs(provider.GoogleOauth2, provider.Registry.get(provider.GoogleOauth2.NAME))

    def test_get_returns_none_if_provider_not_enabled(self):
        self.assertIsNone(provider.Registry.get(provider.MozillaPersona.NAME))
