"""
Serializers for upstream -> downstream entity links.
"""

from rest_framework import serializers

from cms.djangoapps.contentstore.models import PublishableEntityLink


class PublishableEntityLinksSerializer(serializers.ModelSerializer):
    """
    Serializer for publishable entity links.
    """
    upstream_context_title = serializers.CharField(read_only=True)
    upstream_version = serializers.IntegerField(read_only=True)
    ready_to_sync = serializers.BooleanField()

    class Meta:
        model = PublishableEntityLink
        exclude = ['upstream_block', 'uuid']


class PublishableEntityLinksSummarySerializer(serializers.Serializer):
    """
    Serializer for summary for publishable entity links
    """
    upstream_context_title = serializers.CharField(read_only=True)
    upstream_context_key = serializers.CharField(read_only=True)
    ready_to_sync_count = serializers.IntegerField(read_only=True)
    total_count = serializers.IntegerField(read_only=True)
