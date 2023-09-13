"""
API Serializers for course rerun
"""

from rest_framework import serializers


class CourseRerunSerializer(serializers.Serializer):
    """ Serializer for course rerun """
    allow_unicode_course_id = serializers.BooleanField()
    course_creator_status = serializers.CharField()
    display_name = serializers.CharField()
    number = serializers.CharField()
    org = serializers.CharField()
    run = serializers.CharField()
