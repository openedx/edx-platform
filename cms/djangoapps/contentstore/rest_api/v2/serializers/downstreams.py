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


class PublishableEntityLinksUsageKeySerializer(serializers.ModelSerializer):
    """
    Serializer for returning a string list of the usage keys.
    """
    def to_representation(self, instance: PublishableEntityLink) -> str:
        return str(instance.downstream_usage_key)

    class Meta:
        model = PublishableEntityLink
        fields = ('downstream_usage_key')
