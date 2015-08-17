"""
API Serializers
"""
from rest_framework import serializers


class GradingPolicySerializer(serializers.Serializer):
    """ Serializer for course grading policy. """
    assignment_type = serializers.CharField(source='type')
    count = serializers.IntegerField(source='min_count')
    dropped = serializers.IntegerField(source='drop_count')
    weight = serializers.FloatField()


# pylint: disable=invalid-name
class BlockSerializer(serializers.Serializer):
    """ Serializer for course structure block. """
    id = serializers.CharField(source='usage_key')
    type = serializers.CharField(source='block_type')
    parent = serializers.CharField(source='parent')
    display_name = serializers.CharField()
    graded = serializers.BooleanField(default=False)
    format = serializers.CharField()
    children = serializers.CharField()


class CourseStructureSerializer(serializers.Serializer):
    """ Serializer for course structure. """
    root = serializers.CharField(source='root')
    blocks = serializers.SerializerMethodField('get_blocks')

    def get_blocks(self, structure):
        """ Serialize the individual blocks. """
        serialized = {}

        for key, block in structure['blocks'].iteritems():
            serialized[key] = BlockSerializer(block).data

        return serialized
