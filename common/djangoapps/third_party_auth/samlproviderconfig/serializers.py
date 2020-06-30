"""
    Serializer for SAMLProviderConfig
"""

from rest_framework import serializers

from third_party_auth.models import SAMLProviderConfig


class SAMLProviderConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SAMLProviderConfig
        fields = '__all__'
