"""
API Serializers for course home
"""

from rest_framework import serializers

from openedx.core.lib.api.serializers import CourseKeyField

from cms.djangoapps.contentstore.rest_api.serializers.common import CourseCommonSerializer


class UnsucceededCourseSerializer(serializers.Serializer):
    """Serializer for unsucceeded course"""
    display_name = serializers.CharField()
    course_key = CourseKeyField()
    org = serializers.CharField()
    number = serializers.CharField()
    run = serializers.CharField()
    is_failed = serializers.BooleanField()
    is_in_progress = serializers.BooleanField()
    dismiss_link = serializers.CharField()


class CourseHomeTabSerializer(serializers.Serializer):
    archived_courses = CourseCommonSerializer(required=False, many=True)
    courses = CourseCommonSerializer(required=False, many=True)
    in_process_course_actions = UnsucceededCourseSerializer(many=True, required=False, allow_null=True)
