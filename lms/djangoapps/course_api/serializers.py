"""
Course API Serializers.  Representing course catalog data
"""

import urllib

from django.core.urlresolvers import reverse
from rest_framework import serializers


class _MediaSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a media object.
    """
    def __init__(self, uri_attribute, *args, **kwargs):
        super(_MediaSerializer, self).__init__(*args, **kwargs)
        self.uri_attribute = uri_attribute

    uri = serializers.SerializerMethodField(source='*')

    def get_uri(self, course_overview):
        """
        Get the representation for the media resource's URI
        """
        return getattr(course_overview, self.uri_attribute)


class _CourseApiMediaCollectionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a collection of media objects
    """
    course_image = _MediaSerializer(source='*', uri_attribute='course_image_url')
    course_video = _MediaSerializer(source='*', uri_attribute='course_video_url')


class CourseSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects
    """

    course_id = serializers.CharField(source='id', read_only=True)
    name = serializers.CharField(source='display_name_with_default')
    number = serializers.CharField(source='display_number_with_default')
    org = serializers.CharField(source='display_org_with_default')
    short_description = serializers.CharField()
    effort = serializers.CharField()

    media = _CourseApiMediaCollectionSerializer(source='*')

    start = serializers.DateTimeField()
    start_type = serializers.CharField()
    start_display = serializers.CharField()
    end = serializers.DateTimeField()

    enrollment_start = serializers.DateTimeField()
    enrollment_end = serializers.DateTimeField()

    blocks_url = serializers.SerializerMethodField()

    def get_blocks_url(self, course_overview):
        """
        Get the representation for SerializerMethodField `blocks_url`
        """
        base_url = '?'.join([
            reverse('blocks_in_course'),
            urllib.urlencode({'course_id': course_overview.id}),
        ])
        return self.context['request'].build_absolute_uri(base_url)
