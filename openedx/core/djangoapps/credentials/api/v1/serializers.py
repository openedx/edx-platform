"""
Credentials API serializers (v1).
"""

from rest_framework import serializers


class GenerateProgramsCredentialSerializer(serializers.Serializer):
    program_id = serializers.IntegerField(required=True)
    usernames = serializers.CharField(required=True)
    is_whitelist = serializers.BooleanField(default=False)
    whitelist_reason = serializers.CharField(allow_blank=True)
