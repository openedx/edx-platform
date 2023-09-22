"""
API Serializers for videos
"""
from rest_framework import serializers
from .common import StrictSerializer


class FileSpecSerializer(StrictSerializer):
    """ Strict Serializer for file specs """
    file_name = serializers.CharField()
    content_type = serializers.ChoiceField(choices=['video/mp4', 'video/webm', 'video/ogg'])


class VideoUploadSerializer(StrictSerializer):
    """
    Strict Serializer for video upload urls.
    Note that these are not actually video uploads but endpoints to generate an upload url for AWS
    and generating a video placeholder without performing an actual upload.
    """
    files = serializers.ListField(
        child=FileSpecSerializer()
    )


class VideoImageSerializer(StrictSerializer):
    """
    Strict Serializer for video imgage files.
    """
    file = serializers.ImageField()
