"""
Serializers for upstream -> downstream entity links.
"""

from rest_framework import serializers

from cms.djangoapps.contentstore.models import ComponentLink, ContainerLink


class ComponentLinksSerializer(serializers.ModelSerializer):
    """
    Serializer for publishable component entity links.
    """
    upstream_context_title = serializers.CharField(read_only=True)
    upstream_version = serializers.IntegerField(read_only=True, source="upstream_version_num")
    ready_to_sync = serializers.BooleanField()

    class Meta:
        model = ComponentLink
        exclude = ['upstream_block', 'uuid']


class PublishableEntityLinksSummarySerializer(serializers.Serializer):
    """
    Serializer for summary for publishable entity links
    """
    upstream_context_title = serializers.CharField(read_only=True)
    upstream_context_key = serializers.CharField(read_only=True)
    ready_to_sync_count = serializers.IntegerField(read_only=True)
    total_count = serializers.IntegerField(read_only=True)
    last_published_at = serializers.DateTimeField(read_only=True)


class ContainerLinksSerializer(serializers.ModelSerializer):
    """
    Serializer for publishable container entity links.
    """
    upstream_context_title = serializers.CharField(read_only=True)
    upstream_version = serializers.IntegerField(read_only=True, source="upstream_version_num")
    ready_to_sync = serializers.BooleanField()

    class Meta:
        model = ContainerLink
        exclude = ['upstream_container', 'uuid']


class PublishableEntityLinkSerializer(serializers.ModelSerializer):
    """
    Serializer for publishable component or container entity links.
    """

    def to_representation(self, instance):
        if isinstance(instance, ComponentLink):
            return ComponentLinksSerializer(instance).data
        elif isinstance(instance, ContainerLink):
            return ContainerLinksSerializer(instance).data
        raise Exception("Unexpected type")
