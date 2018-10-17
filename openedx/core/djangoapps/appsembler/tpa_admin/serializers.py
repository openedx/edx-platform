import json

from third_party_auth.models import SAMLConfiguration, SAMLProviderConfig, SAMLProviderData
from third_party_auth.models import clean_json

from rest_framework import serializers


class SAMLConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SAMLConfiguration
        fields = (
            'id', 'site', 'enabled', 'entity_id', 'private_key', 'public_key', 'org_info_str', 'other_config_str'
        )

    def validate_private_key(self, value):
        return value.replace("-----BEGIN RSA PRIVATE KEY-----", "").replace("-----BEGIN PRIVATE KEY-----", "").replace(
            "-----END RSA PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").strip()

    def validate_public_key(self, value):
        return value.replace("-----BEGIN CERTIFICATE-----", "").replace("-----END CERTIFICATE-----", "").strip()

    def validate_org_info_str(self, value):
        return clean_json(value, dict)

    def validate_other_config_str(self, value):
        return clean_json(value, dict)


class SAMLProviderConfigSerializer(serializers.ModelSerializer):
    metadata_ready = serializers.SerializerMethodField()

    class Meta:
        model = SAMLProviderConfig
        fields = (
            'id', 'site', 'enabled', 'name', 'icon_class', 'icon_image', 'secondary', 'skip_registration_form',
            'visible', 'skip_email_verification', 'idp_slug', 'entity_id', 'metadata_source', 'attr_user_permanent_id',
            'attr_full_name', 'attr_first_name', 'attr_last_name', 'attr_username', 'attr_email', 'other_settings',
            'metadata_ready'
        )

    def validate_other_settings(self, value):
        return clean_json(value, dict)

    def get_metadata_ready(self, obj):
        """ Do we have cached metadata for this SAML provider? """
        data = SAMLProviderData.current(obj.entity_id)
        return bool(data and data.is_valid())
