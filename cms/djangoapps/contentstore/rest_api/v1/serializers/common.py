"""
Common API Serializers
"""

from rest_framework import serializers

from openedx.core.lib.api.serializers import CourseKeyField


class CourseCommonSerializer(serializers.Serializer):
    """Serializer for course renders"""
    course_key = CourseKeyField()
    display_name = serializers.CharField()
    lms_link = serializers.CharField()
    number = serializers.CharField()
    org = serializers.CharField()
    rerun_link = serializers.CharField()
    run = serializers.CharField()
    url = serializers.CharField()


class ProctoringErrorModelSerializer(serializers.Serializer):
    """
    Serializer for proctoring error model item.
    """
    deprecated = serializers.BooleanField()
    display_name = serializers.CharField()
    help = serializers.CharField()
    hide_on_enabled_publisher = serializers.BooleanField()
    value = serializers.CharField()


class ProctoringErrorListSerializer(serializers.Serializer):
    """
    Serializer for proctoring error list.
    """
    key = serializers.CharField()
    message = serializers.CharField()
    model = ProctoringErrorModelSerializer()
