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
    source_context_title = serializers.CharField(allow_blank=True, source="get_source_context_title")
    olx_url = serializers.HyperlinkedIdentityField(view_name="staged-content-olx", lookup_field="id")

    class Meta:
        model = StagedContent
        fields = [
            'id',
            'user',
            'created',
            'purpose',
            'status',
            'block_type',
            # We don't include OLX; it may be large. But we include the URL to retrieve it.
            'olx_url',
            'display_name',
            'source_context',
            'source_context_title',
        ]


class UserClipboardSerializer(serializers.Serializer):
    """
    Serializer for the status of the user's clipboard
    """
    staged_content = StagedContentSerializer(allow_null=True)
