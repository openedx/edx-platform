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
    ready_to_sync_from_children = serializers.BooleanField()
    top_level_parent_usage_key = serializers.CharField(
        source='top_level_parent.downstream_usage_key',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = ComponentLink
        exclude = ['upstream_block', 'uuid', 'top_level_parent']


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
    ready_to_sync_from_children = serializers.BooleanField()
    top_level_parent_usage_key = serializers.CharField(
        source='top_level_parent.downstream_usage_key',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = ContainerLink
        exclude = ['upstream_container', 'uuid', 'top_level_parent']


class PublishableEntityLinkSerializer(serializers.Serializer):
    """
    Serializer for publishable component or container entity links.
    """
    upstream_key = serializers.CharField(read_only=True)
    upstream_type = serializers.ChoiceField(read_only=True, choices=['component', 'container'])

    def to_representation(self, instance):
        if isinstance(instance, ComponentLink):
            data = ComponentLinksSerializer(instance).data
            data['upstream_key'] = data.get('upstream_usage_key')
            data['upstream_type'] = 'component'
            del data['upstream_usage_key']
        elif isinstance(instance, ContainerLink):
            data = ContainerLinksSerializer(instance).data
            data['upstream_key'] = data.get('upstream_container_key')
            data['upstream_type'] = 'container'
            del data['upstream_container_key']
        else:
            raise Exception("Unexpected type")

        return data
