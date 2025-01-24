"""
Serializers for upstream -> downstream entity links.
"""

from rest_framework import serializers

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class PublishableEntityLinksSerializer(serializers.Serializer):
    """
    Serializer for publishable entity links.
    """
    upstream_usage_key = serializers.CharField(read_only=True)
    upstream_context_key = serializers.CharField(read_only=True)
    upstream_context_title = serializers.CharField(read_only=True)
    upstream_version = serializers.IntegerField(read_only=True)
    downstream_usage_key = serializers.CharField(read_only=True)
    downstream_context_title = serializers.CharField(read_only=True)
    downstream_context_key = serializers.CharField(read_only=True)
    version_synced = serializers.IntegerField(read_only=True)
    version_declined = serializers.IntegerField(read_only=True)
    created = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)
    updated = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)
    ready_to_sync = serializers.SerializerMethodField()

    def get_ready_to_sync(self, obj):
        """Calculate ready_to_sync field"""
        return bool(
            obj.upstream_version and
            obj.upstream_version > (obj.version_synced or 0) and
            obj.upstream_version > (obj.version_declined or 0)
        )
