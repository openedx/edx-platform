"""
API Serializers for videos
"""
from rest_framework import serializers
from .common import StrictSerializer, CourseCommonSerializer


class FileSpecSerializer(StrictSerializer):
    """ Strict Serializer for file specs """
    file_name = serializers.CharField()
    content_type = serializers.ChoiceField(choices=['video/mp4', 'video/webm', 'video/ogg'])


class VideoImageSettingsSerializer(serializers.Serializer):
    video_image_upload_enabled = serializers.BooleanField()
    max_size = serializers.IntegerField()
    min_size = serializers.IntegerField()
    max_width = serializers.IntegerField()
    max_height = serializers.IntegerField()
    supported_file_formats = serializers.DictField(
        child=serializers.CharField()
    )


class VideoTranscriptSettingsSerializer(serializers.Serializer):
    transcript_download_handler_url = serializers.CharField()
    transcript_upload_handler_url = serializers.CharField()
    transcript_delete_handler_url = serializers.CharField()
    trancript_download_file_format = serializers.CharField()
    transcript_preferences_handler_url = serializers.CharField(required=False, allow_null=True)
    transcript_credentials_handler_url = serializers.CharField(required=False, allow_null=True)
    transcription_plans = serializers.DictField(
        child = serializers.DictField(),
        required=False,
        allow_null=True,
    )


class VideoModelSerializer(serializers.Serializer):
    client_video_id = serializers.CharField()
    course_video_image_url = serializers.CharField()
    created = serializers.CharField()
    duration = serializers.FloatField()
    edx_video_id = serializers.CharField()
    error_description = serializers.CharField()
    status = serializers.CharField()
    transcript_urls = serializers.DictField(
        child=serializers.CharField()
    )
    transcription_status = serializers.CharField()
    transcripts = serializers.ListField(
        child=serializers.CharField()
    )

class CourseVideosSerializer(serializers.Serializer):
    """Serializer for course home"""
    # context_course = CourseCommonSerializer()
    image_upload_url = serializers.CharField()
    video_handler_url = serializers.CharField()
    encodings_download_url = serializers.CharField()
    default_video_image_url = serializers.CharField()
    previous_uploads = VideoModelSerializer(many=True, required=False)
    concurrent_upload_limit = serializers.IntegerField()
    video_supported_file_formats = serializers.ListField(
        child=serializers.CharField()
    )
    video_upload_max_file_size = serializers.CharField()
    video_image_settings = VideoImageSettingsSerializer(required=True, allow_null=False)
    is_video_transcript_enabled = serializers.BooleanField()
    active_transcript_preferences = serializers.BooleanField(required=False, allow_null=True)
    transcript_credentials = serializers.DictField(
        child=serializers.CharField()
    )
    transcript_available_languages = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    video_transcript_settings = VideoTranscriptSettingsSerializer()
    pagination_context = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
    )


class VideoDownloadSerializer(serializers.Serializer):
    download_link = serializers.CharField()


class VideoUsageSerializer(serializers.Serializer):
    usage_locations = serializers.ListField(
        child=serializers.CharField()
    )


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
