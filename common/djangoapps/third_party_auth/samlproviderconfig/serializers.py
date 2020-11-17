"""
Serializer for SAMLProviderConfig
"""

from rest_framework import serializers

from common.djangoapps.third_party_auth.models import SAMLProviderConfig, SAMLConfiguration


class SAMLProviderConfigSerializer(serializers.ModelSerializer):
    saml_config_id = serializers.IntegerField(required=False)

    class Meta:
        model = SAMLProviderConfig
        fields = '__all__'

    def create(self, validated_data):
        """
        Overwriting create in order to get a SAMLConfiguration object from id.
        """
        if 'saml_config_id' in validated_data:
            saml_configuration = SAMLConfiguration.objects.current_set().get(id=validated_data['saml_config_id'])
            del validated_data['saml_config_id']
            validated_data['saml_configuration'] = saml_configuration

        return SAMLProviderConfig.objects.create(**validated_data)

    def update(self, instance, validated_data):

        if 'saml_config_id' in validated_data:
            saml_configuration = SAMLConfiguration.objects.current_set().get(id=validated_data['saml_config_id'])
            del validated_data['saml_config_id']
            validated_data['saml_configuration'] = saml_configuration

        for modifiable_field in validated_data:
            setattr(
                instance,
                modifiable_field,
                validated_data.get(modifiable_field, getattr(instance, modifiable_field))
            )
        instance.save()
        return instance
