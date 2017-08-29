"""
Serializers for the completion api
"""

# pylint: disable=abstract-method

from __future__ import absolute_import, division, print_function, unicode_literals


from rest_framework import serializers
import six

from .models import AGGREGATE_CATEGORIES


class _CompletionSerializer(serializers.Serializer):
    """
    Inner serializer for actual completion data.
    """
    earned = serializers.FloatField()
    possible = serializers.FloatField()
    ratio = serializers.FloatField()


class CourseCompletionSerializer(serializers.Serializer):
    """
    Serialize completions at the course level.
    """
    course_key = serializers.CharField()
    completion = _CompletionSerializer(source='*')
    mean = serializers.FloatField()

    optional_fields = {'mean'}

    def __init__(self, instance, requested_fields=frozenset(), *args, **kwargs):
        super(CourseCompletionSerializer, self).__init__(instance, *args, **kwargs)
        for field in self.optional_fields - requested_fields:
            del self.fields[field]


class BlockCompletionSerializer(serializers.Serializer):
    """
    A serializer that represents nested aggregations of sub-graphs
    of xblocks.
    """
    course_key = serializers.CharField()
    block_key = serializers.CharField()
    completion = _CompletionSerializer(source='*')


def native_identifier(string):
    """
    Convert identifiers to the the native str type for the current version of
    python. This is required for the first argument to three-argument-`type()`.

    This function expects all identifiers comprise only ascii characters.
    """
    if six.PY2:
        if isinstance(string, unicode):
            # Python 2 identifiers are required to be ascii
            string = string.encode('ascii')
    elif isinstance(string, bytes):
        # Python 3 identifiers can technically be non-ascii, but don't.
        string = string.decode('ascii')
    return string


def course_completion_serializer_factory(requested_fields):
    """
    Create a CourseCompletionSerializer that nests appropriate
    BlockCompletionSerializers for the specified requested_fields.
    """
    dunder_dict = {
        field: BlockCompletionSerializer(many=True) for field in requested_fields
        if field in AGGREGATE_CATEGORIES
    }
    return type(
        native_identifier('CourseCompletionSerializerWithAggregates'),
        (CourseCompletionSerializer,),
        dunder_dict,
    )
