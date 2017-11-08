import json

from third_party_auth.models import SAMLConfiguration, SAMLProviderConfig, SAMLProviderData

from rest_framework import serializers


class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""
    def to_internal_value(self, data):
        return json.dumps(data)

    def to_representation(self, value):
        return value


class SAMLConfigurationSerializer(serializers.ModelSerializer):
    other_config_str = JSONSerializerField()

    class Meta:
        model = SAMLConfiguration
        fields = (
            'id', 'site', 'enabled','entity_id', 'private_key', 'public_key', 'org_info_str', 'other_config_str'
        )


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

    def get_metadata_ready(self, obj):
        """ Do we have cached metadata for this SAML provider? """
        if not obj.is_active:
            return None  # N/A
        data = SAMLProviderData.current(obj.entity_id)
        return bool(data and data.is_valid())
