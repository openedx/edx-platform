"""Unit tests for provider.py."""

from mock import Mock, patch
from third_party_auth import provider
from third_party_auth.tests import testutil
import unittest


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
class RegistryTest(testutil.TestCase):
    """Tests registry discovery and operation."""

    def test_configure_once_adds_gettable_providers(self):
        facebook_provider = self.configure_facebook_provider(enabled=True)
        # pylint: disable=no-member
        self.assertEqual(facebook_provider.id, provider.Registry.get(facebook_provider.provider_id).id)

    def test_no_providers_by_default(self):
        enabled_providers = provider.Registry.enabled()
        self.assertEqual(len(enabled_providers), 0, "By default, no providers are enabled.")

    def test_runtime_configuration(self):
        self.configure_google_provider(enabled=True)
        enabled_providers = provider.Registry.enabled()
        self.assertEqual(len(enabled_providers), 1)
        self.assertEqual(enabled_providers[0].name, "Google")
        self.assertEqual(enabled_providers[0].secret, "opensesame")

        self.configure_google_provider(enabled=False)
        enabled_providers = provider.Registry.enabled()
        self.assertEqual(len(enabled_providers), 0)

        self.configure_google_provider(enabled=True, secret="alohomora")
        enabled_providers = provider.Registry.enabled()
        self.assertEqual(len(enabled_providers), 1)
        self.assertEqual(enabled_providers[0].secret, "alohomora")

    def test_cannot_load_arbitrary_backends(self):
        """ Test that only backend_names listed in settings.AUTHENTICATION_BACKENDS can be used """
        self.configure_oauth_provider(enabled=True, name="Disallowed", backend_name="disallowed")
        self.enable_saml()
        self.configure_saml_provider(enabled=True, name="Disallowed", idp_slug="test", backend_name="disallowed")
        self.assertEqual(len(provider.Registry.enabled()), 0)

    def test_enabled_returns_list_of_enabled_providers_sorted_by_name(self):
        provider_names = ["Stack Overflow", "Google", "LinkedIn", "GitHub"]
        backend_names = []
        for name in provider_names:
            backend_name = name.lower().replace(' ', '')
            backend_names.append(backend_name)
            self.configure_oauth_provider(enabled=True, name=name, backend_name=backend_name)

        with patch('third_party_auth.provider._PSA_OAUTH2_BACKENDS', backend_names):
            self.assertEqual(sorted(provider_names), [prov.name for prov in provider.Registry.enabled()])

    def test_get_returns_enabled_provider(self):
        google_provider = self.configure_google_provider(enabled=True)
        # pylint: disable=no-member
        self.assertEqual(google_provider.id, provider.Registry.get(google_provider.provider_id).id)

    def test_get_returns_none_if_provider_not_enabled(self):
        linkedin_provider_id = "oa2-linkedin-oauth2"
        # At this point there should be no configuration entries at all so no providers should be enabled
        self.assertEqual(provider.Registry.enabled(), [])
        self.assertIsNone(provider.Registry.get(linkedin_provider_id))
        # Now explicitly disabled this provider:
        self.configure_linkedin_provider(enabled=False)
        self.assertIsNone(provider.Registry.get(linkedin_provider_id))
        self.configure_linkedin_provider(enabled=True)
        self.assertEqual(provider.Registry.get(linkedin_provider_id).provider_id, linkedin_provider_id)

    def test_get_from_pipeline_returns_none_if_provider_not_enabled(self):
        self.assertEqual(provider.Registry.enabled(), [], "By default, no providers are enabled.")
        self.assertIsNone(provider.Registry.get_from_pipeline(Mock()))

    def test_get_enabled_by_backend_name_returns_enabled_provider(self):
        google_provider = self.configure_google_provider(enabled=True)
        found = list(provider.Registry.get_enabled_by_backend_name(google_provider.backend_name))
        self.assertEqual(found, [google_provider])

    def test_get_enabled_by_backend_name_returns_none_if_provider_not_enabled(self):
        google_provider = self.configure_google_provider(enabled=False)
        found = list(provider.Registry.get_enabled_by_backend_name(google_provider.backend_name))
        self.assertEqual(found, [])
