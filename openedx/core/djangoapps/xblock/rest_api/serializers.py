"""
Serializers for the xblock REST API
"""
from rest_framework import serializers


class XBlockOlxSerializer(serializers.Serializer):
    """
    Serializer for representing an XBlock's OLX
    """
    olx = serializers.CharField()
