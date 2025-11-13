"""
Django admin configuration for AI Learning models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AdaptiveInteraction,
    AIEngineWebhook,
    AIGeneratedCourse,
    StudentLearningProfile,
)


@admin.register(AIGeneratedCourse)
class AIGeneratedCourseAdmin(admin.ModelAdmin):
    """Admin for AI-generated courses."""

    list_display = [
        'course_key',
        'creator',
        'generation_status',
        'created',
        'modified'
    ]
    list_filter = ['generation_status', 'created']
    search_fields = [
        'course_key',
        'creator__username',
        'generation_prompt',
        'ai_engine_course_id'
    ]
    readonly_fields = [
        'course_key',
        'creator',
        'ai_engine_course_id',
        'created',
        'modified',
        'formatted_curriculum'
    ]

    fieldsets = (
        ('Course Information', {
            'fields': ('course_key', 'creator', 'ai_engine_course_id')
        }),
        ('Generation Details', {
            'fields': ('generation_prompt', 'generation_status', 'formatted_curriculum')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )

    def formatted_curriculum(self, obj):
        """Format curriculum data for display."""
        import json
        if obj.curriculum_data:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.curriculum_data, indent=2)
            )
        return "No curriculum data available"
    formatted_curriculum.short_description = 'Curriculum Data'


@admin.register(StudentLearningProfile)
class StudentLearningProfileAdmin(admin.ModelAdmin):
    """Admin for student learning profiles."""

    list_display = [
        'user',
        'learning_style',
        'mastered_count',
        'struggling_count',
        'last_sync',
        'created'
    ]
    list_filter = ['learning_style', 'last_sync']
    search_fields = ['user__username', 'user__email', 'ai_engine_profile_id']
    readonly_fields = [
        'user',
        'ai_engine_profile_id',
        'last_sync',
        'created',
        'modified',
        'formatted_mastered',
        'formatted_struggling'
    ]

    fieldsets = (
        ('Student Information', {
            'fields': ('user', 'ai_engine_profile_id', 'learning_style')
        }),
        ('Learning Progress', {
            'fields': ('formatted_mastered', 'formatted_struggling')
        }),
        ('Preferences', {
            'fields': ('preferences',),
            'classes': ('collapse',)
        }),
        ('Sync Information', {
            'fields': ('last_sync', 'created', 'modified')
        }),
    )

    def mastered_count(self, obj):
        """Number of mastered concepts."""
        return len(obj.mastered_concepts)
    mastered_count.short_description = 'Mastered'

    def struggling_count(self, obj):
        """Number of struggling concepts."""
        return len(obj.struggling_concepts)
    struggling_count.short_description = 'Struggling'

    def formatted_mastered(self, obj):
        """Format mastered concepts list."""
        if obj.mastered_concepts:
            return format_html(
                '<ul>{}</ul>',
                format_html_join('', '<li>{}</li>', ((c,) for c in obj.mastered_concepts))
            )
        return "None"
    formatted_mastered.short_description = 'Mastered Concepts'

    def formatted_struggling(self, obj):
        """Format struggling concepts list."""
        if obj.struggling_concepts:
            return format_html(
                '<ul>{}</ul>',
                format_html_join('', '<li>{}</li>', ((c,) for c in obj.struggling_concepts))
            )
        return "None"
    formatted_struggling.short_description = 'Struggling Concepts'


@admin.register(AdaptiveInteraction)
class AdaptiveInteractionAdmin(admin.ModelAdmin):
    """Admin for adaptive interactions."""

    list_display = [
        'user',
        'course_key',
        'interaction_type',
        'response_time_ms',
        'created'
    ]
    list_filter = ['interaction_type', 'created']
    search_fields = [
        'user__username',
        'course_key',
        'usage_key'
    ]
    readonly_fields = [
        'user',
        'course_key',
        'usage_key',
        'interaction_type',
        'response_time_ms',
        'created',
        'modified',
        'formatted_interaction_data',
        'formatted_ai_response'
    ]

    fieldsets = (
        ('Interaction Details', {
            'fields': (
                'user',
                'course_key',
                'usage_key',
                'interaction_type',
                'created'
            )
        }),
        ('Data', {
            'fields': (
                'formatted_interaction_data',
                'formatted_ai_response',
                'response_time_ms'
            )
        }),
    )

    def formatted_interaction_data(self, obj):
        """Format interaction data for display."""
        import json
        if obj.interaction_data:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.interaction_data, indent=2)
            )
        return "No data"
    formatted_interaction_data.short_description = 'Interaction Data'

    def formatted_ai_response(self, obj):
        """Format AI response for display."""
        import json
        if obj.ai_response:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.ai_response, indent=2)
            )
        return "No response"
    formatted_ai_response.short_description = 'AI Response'


@admin.register(AIEngineWebhook)
class AIEngineWebhookAdmin(admin.ModelAdmin):
    """Admin for AI Engine webhooks."""

    list_display = [
        'webhook_type',
        'status',
        'created',
        'has_error'
    ]
    list_filter = ['webhook_type', 'status', 'created']
    search_fields = ['webhook_type', 'payload', 'error_message']
    readonly_fields = [
        'webhook_type',
        'status',
        'created',
        'modified',
        'formatted_payload'
    ]

    fieldsets = (
        ('Webhook Information', {
            'fields': ('webhook_type', 'status', 'created', 'modified')
        }),
        ('Payload', {
            'fields': ('formatted_payload',)
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )

    def has_error(self, obj):
        """Check if webhook has an error."""
        return bool(obj.error_message)
    has_error.boolean = True
    has_error.short_description = 'Error'

    def formatted_payload(self, obj):
        """Format payload for display."""
        import json
        if obj.payload:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.payload, indent=2)
            )
        return "No payload"
    formatted_payload.short_description = 'Payload'
