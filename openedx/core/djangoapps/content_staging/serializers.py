"""
Serializers for the content libraries REST API
"""
from rest_framework import serializers

from .models import StagedContent


class StagedContentSerializer(serializers.ModelSerializer):
    """
    Serializer for staged content. Doesn't include the OLX by default.
    """
    # The title of the course that the content came from originally, if relevant
    source_context_title = serializers.CharField(allow_blank=True)

    class Meta:
        model = StagedContent
        fields = [
            'id',
            'user',
            'created',
            'purpose',
            'status',
            'block_type',
            # We don't include OLX; it may be large
            'display_name',
            'source_context',
        ]


class UserClipboardSerializer(serializers.Serializer):
    """
    Serializer for the status of the user's clipboard
    """
    staged_content = StagedContentSerializer(allow_null=True)
