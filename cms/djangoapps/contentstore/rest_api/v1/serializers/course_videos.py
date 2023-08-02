
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class CourseVideosSerializer(serializers.Serializer):
    """ Serializer for course videos """
    edx_video_id = serializers.CharField(read_only=True, help_text=_("ID of the video"))
    client_video_id = serializers.CharField(help_text=_("Client ID of the video"))
    created = serializers.DateTimeField(read_only=True, help_text=_("Creation timestamp of video"))
    duration = serializers.FloatField(read_only=True, help_text=_("Duration of video in seconds"))
    status = serializers.CharField(read_only=True, help_text=_("Status of video in processing pipeline"))
    course_video_image_url = serializers.URLField(read_only=True, help_text=_("Video poster image"))


