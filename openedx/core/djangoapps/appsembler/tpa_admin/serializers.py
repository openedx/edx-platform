from third_party_auth.models import SAMLConfiguration, SAMLProviderConfig

from rest_framework import serializers

class SAMLConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SAMLConfiguration
        fields = ('id', 'site', 'enabled','entity_id', 'private_key', 'public_key', 'org_info_str', 'other_config_str')


class SAMLProviderConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = SAMLProviderConfig
        fields = (
        'id', 'site', 'enabled', 'name', 'icon_class', 'icon_image', 'secondary', 'skip_registration_form', 'visible',
        'skip_email_verification', 'idp_slug', 'entity_id', 'metadata_source', 'attr_user_permanent_id',
        'attr_full_name', 'attr_first_name', 'attr_last_name', 'attr_username', 'attr_email', 'other_settings')