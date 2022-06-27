"""
Tests for third_party_auth/models.py.
"""
import pytest
from django.test import TestCase
from django.db.utils import IntegrityError

from .factories import SAMLProviderConfigFactory
from ..models import SAMLProviderConfig


class TestSamlProviderConfigModel(TestCase):
    """
    Test model operations for the saml provider config model.
    """

    def setUp(self):
        super().setUp()
        self.saml_provider_config = SAMLProviderConfigFactory()

    def test_unique_entity_id_enforcement_for_non_current_configs(self):
        """
        Test that the unique entity ID enforcement does not apply to noncurrent configs
        """
        assert len(SAMLProviderConfig.objects.all()) == 1
        old_entity_id = self.saml_provider_config.entity_id
        self.saml_provider_config.entity_id = f'{self.saml_provider_config.entity_id}-ayylmao'
        self.saml_provider_config.save()

        # check that we now have two records, one non-current
        assert len(SAMLProviderConfig.objects.all()) == 2
        assert len(SAMLProviderConfig.objects.current_set()) == 1

        # Make sure we can use that old entity id
        SAMLProviderConfigFactory(entity_id=old_entity_id)

        # Now if we try and create a new model using a current entity ID then it should throw the integrity error
        with pytest.raises(IntegrityError):
            bad_config = SAMLProviderConfig(entity_id=self.saml_provider_config.entity_id)
            bad_config.save()
