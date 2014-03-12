"""
Test configuration of providers.
"""

from third_party_auth import provider
from third_party_auth.tests import testutil


class RegistryTest(testutil.TestCase):
    """Tests registry discovery and operation."""

    # Allow access to protected methods (or module-protected methods) under
    # test.
    # pylint: disable-msg=protected-access

    def test_calling_configure_once_twice_raises_value_error(self):
        provider.Registry.configure_once([provider.GoogleOauth2.NAME])

        with self.assertRaisesRegexp(ValueError, '^.*already configured$'):
            provider.Registry.configure_once([provider.GoogleOauth2.NAME])

    def test_configure_once_adds_gettable_providers(self):
        provider.Registry.configure_once([provider.GoogleOauth2.NAME])
        self.assertIs(provider.GoogleOauth2, provider.Registry.get(provider.GoogleOauth2.NAME))

    def test_configuring_provider_with_no_implementation_raises_value_error(self):
        with self.assertRaisesRegexp(ValueError, '^.*no_implementation$'):
            provider.Registry.configure_once(['no_implementation'])

    def test_configuring_single_provider_twice_raises_value_error(self):
        provider.Registry._enable(provider.GoogleOauth2)

        with self.assertRaisesRegexp(ValueError, '^.*already enabled'):
            provider.Registry.configure_once([provider.GoogleOauth2.NAME])

    def test_custom_provider_can_be_enabled(self):
        name = 'CustomProvider'

        with self.assertRaisesRegexp(ValueError, '^No implementation.*$'):
            provider.Registry.configure_once([name])

        class CustomProvider(provider.BaseProvider):
            """Custom class to ensure BaseProvider children outside provider can be enabled."""

            NAME = name

        provider.Registry._reset()
        provider.Registry.configure_once([CustomProvider.NAME])
        self.assertEqual([CustomProvider], provider.Registry.enabled())

    def test_enabled_raises_runtime_error_if_not_configured(self):
        with self.assertRaisesRegexp(RuntimeError, '^.*not configured$'):
            provider.Registry.enabled()

    def test_enabled_returns_list_of_enabled_providers_sorted_by_name(self):
        all_providers = provider.Registry._get_all()
        provider.Registry.configure_once(all_providers.keys())
        self.assertEqual(
            sorted(all_providers.values(), key=lambda provider: provider.NAME), provider.Registry.enabled())

    def test_get_raises_runtime_error_if_not_configured(self):
        with self.assertRaisesRegexp(RuntimeError, '^.*not configured$'):
            provider.Registry.get('anything')

    def test_get_returns_enabled_provider(self):
        provider.Registry.configure_once([provider.GoogleOauth2.NAME])
        self.assertIs(provider.GoogleOauth2, provider.Registry.get(provider.GoogleOauth2.NAME))

    def test_get_returns_none_if_provider_not_enabled(self):
        provider.Registry.configure_once([])
        self.assertIsNone(provider.Registry.get(provider.LinkedInOauth2.NAME))
