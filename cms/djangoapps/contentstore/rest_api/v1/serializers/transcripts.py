"""
API Serializers for transcripts
"""
from rest_framework import serializers
from .common import StrictSerializer


class TranscriptSerializer(StrictSerializer):
    """
    Strict Serializer for video transcripts.
    """
    file = serializers.FileField()
    edx_video_id = serializers.CharField()
    language_code = serializers.CharField(required=False, allow_null=True)
    new_language_code = serializers.CharField(required=False, allow_null=True)
