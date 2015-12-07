"""
API Serializers
"""
from collections import defaultdict

from rest_framework import serializers


class GradingPolicySerializer(serializers.Serializer):
    """ Serializer for course grading policy. """
    assignment_type = serializers.CharField(source='type')
    count = serializers.IntegerField(source='min_count')
    dropped = serializers.IntegerField(source='drop_count')
    weight = serializers.FloatField()

    def to_representation(self, obj):
        """
        Return a representation of the grading policy.
        """
        # Backwards compatibility with the behavior of DRF v2.
        # When the grader dictionary was missing keys, DRF v2 would default to None;
        # DRF v3 unhelpfully raises an exception.
        return dict(
            super(GradingPolicySerializer, self).to_representation(
                defaultdict(lambda: None, obj)
            )
        )


# pylint: disable=invalid-name
class BlockSerializer(serializers.Serializer):
    """ Serializer for course structure block. """
    id = serializers.CharField(source='usage_key')
    type = serializers.CharField(source='block_type')
    parent = serializers.CharField(required=False)
    display_name = serializers.CharField()
    graded = serializers.BooleanField(default=False)
    format = serializers.CharField()
    children = serializers.CharField()

    def to_representation(self, obj):
        """
        Return a representation of the block.

        NOTE: this method maintains backwards compatibility with the behavior
        of Django Rest Framework v2.
        """
        data = super(BlockSerializer, self).to_representation(obj)

        # Backwards compatibility with the behavior of DRF v2
        # Include a NULL value for "parent" in the representation
        # (instead of excluding the key entirely)
        if obj.get("parent") is None:
            data["parent"] = None

        # Backwards compatibility with the behavior of DRF v2
        # Leave the children list as a list instead of serializing
        # it to a string.
        data["children"] = obj["children"]

        return data


class CourseStructureSerializer(serializers.Serializer):
    """ Serializer for course structure. """
    root = serializers.CharField()
    blocks = serializers.SerializerMethodField()

    def get_blocks(self, structure):
        """ Serialize the individual blocks. """
        serialized = {}

        for key, block in structure['blocks'].iteritems():
            serialized[key] = BlockSerializer(block).data

        return serialized
