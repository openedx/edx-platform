"""
Serializers for TwoU widget context.
"""

from rest_framework import serializers


class TwoUWidgetContextSerializer(serializers.Serializer):
    """Serializer for TwoU widget context."""

    countryCode = serializers.CharField(allow_blank=True)
