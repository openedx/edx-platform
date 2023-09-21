"""
API Serializers for assets
"""
from rest_framework import serializers
from .common import StrictSerializer


class AssetSerializer(StrictSerializer):
    """
    Strict Serializer for file assets.
    """
    file=serializers.FileField()
