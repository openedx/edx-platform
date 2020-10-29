"""
    Serializer for SAMLProviderData
"""

from rest_framework import serializers

from common.djangoapps.third_party_auth.models import SAMLProviderData


class SAMLProviderDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SAMLProviderData
        fields = '__all__'
