"""
Serializers for the Agreements app
"""
from rest_framework import serializers

from openedx.core.djangoapps.agreements.models import IntegritySignature, LTIPIISignature
from openedx.core.lib.api.serializers import CourseKeyField


class IntegritySignatureSerializer(serializers.ModelSerializer):
    """
    Serializer for the IntegritySignature model
    """
    username = serializers.CharField(source='user.username')
    course_id = CourseKeyField(source='course_key')
    created_at = serializers.DateTimeField(source='created')

    class Meta:
        model = IntegritySignature()
        fields = ('username', 'course_id', 'created_at')


class LTIPIISignatureSerializer(serializers.ModelSerializer):
    """
    Serializer for LTIPIISignature model
    """
    username = serializers.CharField(source='user.username')
    course_id = CourseKeyField(source='course_key')
    created_at = serializers.DateTimeField(source='created')

    class Meta:
        model = LTIPIISignature
        fields = ('username', 'course_id', 'lti_tools', 'created_at')
