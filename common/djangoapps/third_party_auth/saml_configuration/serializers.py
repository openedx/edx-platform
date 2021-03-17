"""
Serializer for SAMLConfiguration
"""

from rest_framework import serializers

from common.djangoapps.third_party_auth.models import SAMLConfiguration


class SAMLConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SAMLConfiguration
        fields = ('id', 'slug')
