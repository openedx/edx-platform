"""
API Serializers for Course Optimizer
"""

from rest_framework import serializers


class LinkCheckBlockSerializer(serializers.Serializer):
    """ Serializer for broken links block model data """
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    display_name = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    url = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    broken_links = serializers.ListField(required=True)

class LinkCheckUnitSerializer(serializers.Serializer):
    """ Serializer for broken links unit model data """
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    display_name = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    blocks = LinkCheckBlockSerializer(many=True)

class LinkCheckSubsectionSerializer(serializers.Serializer):
    """ Serializer for broken links subsection model data """
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    display_name = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    units = LinkCheckUnitSerializer(many=True)

class LinkCheckSectionSerializer(serializers.Serializer):
    """ Serializer for broken links section model data """
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    display_name = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    subsections = LinkCheckSubsectionSerializer(many=True)

class LinkCheckOutputSerializer(serializers.Serializer):
    """ Serializer for broken links output model data """
    sections = LinkCheckSectionSerializer(many=True)

class LinkCheckSerializer(serializers.Serializer):
    """ Serializer for broken links """
    status = serializers.CharField()
    output = LinkCheckOutputSerializer()
