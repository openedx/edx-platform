"""
Serializers for AI Learning API endpoints.
"""

from rest_framework import serializers


class CourseGenerationRequestSerializer(serializers.Serializer):
    """Serializer for course generation requests."""
    prompt = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Natural language description of the desired course"
    )
    course_org = serializers.CharField(
        required=True,
        max_length=64,
        help_text="Organization identifier"
    )
    course_number = serializers.CharField(
        required=True,
        max_length=64,
        help_text="Course number"
    )
    course_run = serializers.CharField(
        required=True,
        max_length=64,
        help_text="Course run identifier"
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional metadata for course generation"
    )


class InteractionRecordSerializer(serializers.Serializer):
    """Serializer for recording adaptive interactions."""
    course_key = serializers.CharField(
        required=True,
        help_text="Course identifier"
    )
    usage_key = serializers.CharField(
        required=True,
        help_text="XBlock identifier"
    )
    interaction_type = serializers.ChoiceField(
        required=True,
        choices=['assessment', 'tutor_chat', 'content_view', 'adaptation'],
        help_text="Type of interaction"
    )
    interaction_data = serializers.JSONField(
        required=True,
        help_text="Data about the interaction"
    )


class AdaptiveFeedbackRequestSerializer(serializers.Serializer):
    """Serializer for adaptive feedback requests."""
    course_key = serializers.CharField(
        required=True,
        help_text="Course identifier"
    )
    usage_key = serializers.CharField(
        required=True,
        help_text="XBlock identifier"
    )
    question = serializers.JSONField(
        required=True,
        help_text="Question data including text, options, etc."
    )
    answer = serializers.JSONField(
        required=True,
        help_text="Student's answer data including response, time taken, etc."
    )


class AITutorRequestSerializer(serializers.Serializer):
    """Serializer for AI tutor chat requests."""
    course_key = serializers.CharField(
        required=True,
        help_text="Course identifier"
    )
    usage_key = serializers.CharField(
        required=True,
        help_text="XBlock identifier where tutor is embedded"
    )
    message = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Student's message to the tutor"
    )
    conversation_history = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="Previous messages in the conversation"
    )
