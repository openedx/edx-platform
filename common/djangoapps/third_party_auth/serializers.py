from rest_framework import serializers

from .models import SAMLProviderConfig

class SAMLProviderConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SAMLProviderConfig
        fields = '__all__'
