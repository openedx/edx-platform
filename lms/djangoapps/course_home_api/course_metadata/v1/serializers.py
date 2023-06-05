# pylint: disable=abstract-method
"""
Course Home Course Metadata Serializers. Returns Course Metadata used for all
Course Home pages.
"""


from django.urls import reverse
from rest_framework import serializers


class CourseTabSerializer(serializers.Serializer):
    """
    Serializer for the Course Home Tabs
    """
    tab_id = serializers.CharField()
    title = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_title(self, tab):
        return tab.title or tab.get('name', '')

    def get_url(self, tab):
        request = self.context.get('request')
        return request.build_absolute_uri(tab.link_func(self.context.get('course'), reverse))


class CourseHomeMetadataSerializer(serializers.Serializer):
    """
    Serializer for the Course Home Course Metadata
    """
    course_id = serializers.CharField()
    is_enrolled = serializers.BooleanField()
    is_self_paced = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    number = serializers.CharField()
    org = serializers.CharField()
    original_user_is_staff = serializers.BooleanField()
    tabs = CourseTabSerializer(many=True)
    title = serializers.CharField()
