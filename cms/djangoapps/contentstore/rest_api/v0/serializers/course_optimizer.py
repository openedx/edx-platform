"""
API Serializers for Course Optimizer
"""

from rest_framework import serializers


class LinkCheckBlockSerializer(serializers.Serializer):
    """ Serializer for broken links block model data """
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    displayName = serializers.CharField(required=True, allow_null=False, allow_blank=True)
    url = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    brokenLinks = serializers.ListField(required=False)
    lockedLinks = serializers.ListField(required=False)
    externalForbiddenLinks = serializers.ListField(required=False)


class LinkCheckUnitSerializer(serializers.Serializer):
    """ Serializer for broken links unit model data """
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    displayName = serializers.CharField(required=True, allow_null=False, allow_blank=True)
    blocks = LinkCheckBlockSerializer(many=True)


class LinkCheckSubsectionSerializer(serializers.Serializer):
    """ Serializer for broken links subsection model data """
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    displayName = serializers.CharField(required=True, allow_null=False, allow_blank=True)
    units = LinkCheckUnitSerializer(many=True)


class LinkCheckSectionSerializer(serializers.Serializer):
    """ Serializer for broken links section model data """
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    displayName = serializers.CharField(required=True, allow_null=False, allow_blank=True)
    subsections = LinkCheckSubsectionSerializer(many=True)


class LinkCheckOutputSerializer(serializers.Serializer):
    """ Serializer for broken links output model data """
    sections = LinkCheckSectionSerializer(many=True)


class LinkCheckSerializer(serializers.Serializer):
    """ Serializer for broken links """
    LinkCheckStatus = serializers.CharField(required=True)
    LinkCheckCreatedAt = serializers.DateTimeField(required=False)
    LinkCheckOutput = LinkCheckOutputSerializer(required=False)
    LinkCheckError = serializers.CharField(required=False)
