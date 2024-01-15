"""
API Serializers for unit page
"""

from django.urls import reverse
from rest_framework import serializers

from cms.djangoapps.contentstore.helpers import (
    xblock_studio_url,
    xblock_type_display_name,
)


class ChildAncestorSerializer(serializers.Serializer):
    """
    Serializer for representing child blocks in the ancestor XBlock.
    """

    url = serializers.SerializerMethodField()
    display_name = serializers.CharField(source="display_name_with_default")

    def get_url(self, obj):
        """
        Method to generate studio URL for the child block.
        """
        return xblock_studio_url(obj)


class AncestorXBlockSerializer(serializers.Serializer):
    """
    Serializer for representing the ancestor XBlock and its children.
    """

    children = ChildAncestorSerializer(many=True)
    title = serializers.CharField()
    is_last = serializers.BooleanField()


class ContainerXBlock(serializers.Serializer):
    """
    Serializer for representing XBlock data. Doesn't include all data about XBlock.
    """

    display_name = serializers.CharField(source="display_name_with_default")
    display_type = serializers.SerializerMethodField()
    category = serializers.CharField()

    def get_display_type(self, obj):
        """
        Method to get the display type name for the container XBlock.
        """
        return xblock_type_display_name(obj)


class ContainerHandlerSerializer(serializers.Serializer):
    """
    Serializer for container handler
    """

    language_code = serializers.CharField()
    action = serializers.CharField()
    xblock = ContainerXBlock()
    is_unit_page = serializers.BooleanField()
    is_collapsible = serializers.BooleanField()
    position = serializers.IntegerField(min_value=1)
    prev_url = serializers.CharField(allow_null=True)
    next_url = serializers.CharField(allow_null=True)
    new_unit_category = serializers.CharField()
    outline_url = serializers.CharField()
    ancestor_xblocks = AncestorXBlockSerializer(many=True)
    component_templates = serializers.ListField(child=serializers.DictField())
    xblock_info = serializers.DictField()
    draft_preview_link = serializers.CharField()
    published_preview_link = serializers.CharField()
    show_unit_tags = serializers.BooleanField()
    user_clipboard = serializers.DictField()
    is_fullwidth_content = serializers.BooleanField()
    assets_url = serializers.SerializerMethodField()
    unit_block_id = serializers.CharField(source="unit.location.block_id")
    subsection_location = serializers.CharField(source="subsection.location")

    def get_assets_url(self, obj):
        """
        Method to get the assets URL based on the course id.
        """

        context_course = obj.get("context_course", None)
        if context_course:
            return reverse(
                "assets_handler", kwargs={"course_key_string": context_course.id}
            )
        return None


class ChildVerticalContainerSerializer(serializers.Serializer):
    """
    Serializer for representing a xblock child of vertical container.
    """

    name = serializers.CharField(source="display_name_with_default")
    block_id = serializers.CharField(source="location")


class VerticalContainerSerializer(serializers.Serializer):
    """
    Serializer for representing a vertical container with state and children.
    """

    children = ChildVerticalContainerSerializer(many=True)
    is_published = serializers.BooleanField()
