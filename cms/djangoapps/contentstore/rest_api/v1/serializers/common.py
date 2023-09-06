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
