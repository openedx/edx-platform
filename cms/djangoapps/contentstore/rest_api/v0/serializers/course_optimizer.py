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
    previousRunLinks = serializers.ListField(required=False)


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
    course_updates = LinkCheckBlockSerializer(many=True, required=False)
    custom_pages = LinkCheckBlockSerializer(many=True, required=False)


class LinkCheckSerializer(serializers.Serializer):
    """ Serializer for broken links """
    LinkCheckStatus = serializers.CharField(required=True)
    LinkCheckCreatedAt = serializers.DateTimeField(required=False)
    LinkCheckOutput = LinkCheckOutputSerializer(required=False)
    LinkCheckError = serializers.CharField(required=False)


class CourseRerunLinkDataSerializer(serializers.Serializer):
    """ Serializer for individual course rerun link data """
    url = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    type = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)


class CourseRerunLinkUpdateRequestSerializer(serializers.Serializer):
    """ Serializer for course rerun link update request """
    action = serializers.ChoiceField(choices=['all', 'specific'], required=True)
    data = CourseRerunLinkDataSerializer(many=True, required=False)

    def validate(self, attrs):
        """
        Validate that data is provided when action is 'specific'
        """
        if attrs.get('action') == 'specific' and not attrs.get('data'):
            raise serializers.ValidationError(
                "Field 'data' is required when action is 'specific'"
            )
        return attrs


class CourseRerunLinkUpdateResultSerializer(serializers.Serializer):
    """ Serializer for individual course rerun link update result """
    new_url = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    type = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    id = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    success = serializers.BooleanField(required=True)
    error_message = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def to_representation(self, instance):
        """
        Override to exclude error_message field when success is True or error_message is null/empty
        """
        data = super().to_representation(instance)
        if data.get('success') is True or not data.get('error_message'):
            data.pop('error_message', None)

        return data


class CourseRerunLinkUpdateStatusSerializer(serializers.Serializer):
    """ Serializer for course rerun link update status """
    status = serializers.ChoiceField(
        choices=['pending', 'in_progress', 'completed', 'failed', 'uninitiated'],
        required=True
    )
    results = CourseRerunLinkUpdateResultSerializer(many=True, required=False)
