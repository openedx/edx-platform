"""
Tests for third_party_auth/models.py.
"""
import unittest
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
import mock

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from .factories import SAMLProviderConfigFactory, SAMLConfigurationFactory
from ..models import SAMLProviderConfig, SAMLConfiguration, SAMLProviderData, USE_LATEST_SAML_CONFIG, clean_username


class TestSamlProviderConfigModel(TestCase, unittest.TestCase):
    """
    Test model operations for the saml provider config model.
    """

    def setUp(self):
        super().setUp()
        self.saml_provider_config = SAMLProviderConfigFactory()

        # Setup for SAML configuration dynamic lookup test
        self.site = SiteFactory()

        # Create initial SAML configuration using the factory
        self.initial_config = SAMLConfigurationFactory(
            site=self.site,
            slug='test-config',
            entity_id='https://initial-entity-id.example.com',
            private_key='initial_private_key',
            public_key='initial_public_key',
        )
        self.initial_config_id = self.initial_config.id

        # Create provider that points to the initial config
        self.provider_config = SAMLProviderConfigFactory(
            site=self.site,
            entity_id='https://test-idp.example.com',
            metadata_source='https://test-idp.example.com/metadata.xml',
            saml_configuration=self.initial_config
        )

        # Create provider data to avoid AuthNotConfigured error
        SAMLProviderData.objects.create(
            entity_id=self.provider_config.entity_id,
            sso_url='https://test-idp.example.com/SSO',
            public_key='test_public_key',
            fetched_at=timezone.now()
        )

    def test_unique_entity_id_enforcement_for_non_current_configs(self):
        """
        Test that the unique entity ID enforcement does not apply to noncurrent configs
        """
        with self.assertLogs() as ctx:
            assert len(SAMLProviderConfig.objects.all()) == 1
            old_entity_id = self.saml_provider_config.entity_id
            self.saml_provider_config.entity_id = f'{self.saml_provider_config.entity_id}-ayylmao'
            self.saml_provider_config.save()

            # check that we now have two records, one non-current
            assert len(SAMLProviderConfig.objects.all()) == 2
            assert len(SAMLProviderConfig.objects.current_set()) == 1

            # Make sure we can use that old entity id
            SAMLProviderConfigFactory(entity_id=old_entity_id)

            # 7/21/22 : Disabling the exception on duplicate entity ID's because of existing data.
            # with pytest.raises(IntegrityError):
            bad_config = SAMLProviderConfig(entity_id=self.saml_provider_config.entity_id)
            bad_config.save()
        assert ctx.records[0].msg == f'Entity ID: {self.saml_provider_config.entity_id} already in use'

    @override_settings(FEATURES={'ENABLE_UNICODE_USERNAME': False})
    def test_clean_username_unicode_disabled(self):
        """
        Test the username cleaner function with unicode disabled
        """
        assert clean_username('ItJüstWòrks™') == 'ItJ_stW_rks'

    @override_settings(FEATURES={'ENABLE_UNICODE_USERNAME': True})
    def test_clean_username_unicode_enabled(self):
        """
        Test the username cleaner function with unicode enabled
        """
        assert clean_username('ItJüstWòrks™') == 'ItJüstWòrks'

    def test_saml_configuration_dynamic_lookup(self):
        """
        Test SAML configuration lookup functionality, including the toggle behavior and error handling.
        """

        # Update configuration creates a new record with the same slug
        self.initial_config.entity_id = 'https://updated-entity-id.example.com'
        self.initial_config.change_date = timezone.now() + timedelta(minutes=5)
        self.initial_config.save()
        self.initial_config.refresh_from_db()

        # Verify we have two configs with the same slug
        config_count = SAMLConfiguration.objects.filter(slug='test-config').count()
        self.assertEqual(config_count, 2)

        # Test with toggle ENABLED - should use latest config
        with mock.patch.object(USE_LATEST_SAML_CONFIG, 'is_enabled', return_value=True):
            provider_idp = self.provider_config.get_config()
            latest_config = SAMLConfiguration.objects.filter(
                slug='test-config', enabled=True
            ).order_by('-change_date').first()

            # Compare the actual objects rather than just IDs
            self.assertEqual(
                provider_idp.conf.get('saml_sp_configuration'),
                latest_config
            )
            self.assertEqual(
                provider_idp.conf.get('saml_sp_configuration').entity_id,
                'https://updated-entity-id.example.com'
            )

        # Test with toggle DISABLED - should use direct config
        with mock.patch.object(USE_LATEST_SAML_CONFIG, 'is_enabled', return_value=False):
            provider_idp = self.provider_config.get_config()
            self.assertEqual(
                provider_idp.conf.get('saml_sp_configuration'),
                self.provider_config.saml_configuration
            )

        # Test error handling
        with mock.patch('common.djangoapps.third_party_auth.models.SAMLConfiguration.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception("Test error")
            with mock.patch.object(USE_LATEST_SAML_CONFIG, 'is_enabled', return_value=True):
                provider_idp = self.provider_config.get_config()
                self.assertEqual(
                    provider_idp.conf.get('saml_sp_configuration'),
                    self.provider_config.saml_configuration
                )

        # Test default fallback
        self.provider_config.saml_configuration = None
        self.provider_config.save()
        default_config = SAMLConfigurationFactory(
            site=self.site,
            slug='default',
            enabled=True,
            entity_id='https://default-entity-id.example.com',
        )
        provider_idp = self.provider_config.get_config()
        self.assertEqual(
            provider_idp.conf.get('saml_sp_configuration'),
            default_config
        )
        self.assertEqual(
            provider_idp.conf.get('saml_sp_configuration').entity_id,
            'https://default-entity-id.example.com'
        )
