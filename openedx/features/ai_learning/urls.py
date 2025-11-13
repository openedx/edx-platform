"""
URL routing for AI Learning integration.
"""

from django.urls import path

from .views import (
    AIEngineWebhookView,
    AITutorChatView,
    AdaptiveFeedbackView,
    GenerateCourseView,
    RecordInteractionView,
    health_check,
)

app_name = 'ai_learning'

urlpatterns = [
    # Course generation
    path(
        'api/v1/courses/generate/',
        GenerateCourseView.as_view(),
        name='generate_course'
    ),

    # Adaptive interactions
    path(
        'api/v1/interactions/record/',
        RecordInteractionView.as_view(),
        name='record_interaction'
    ),

    # Adaptive feedback
    path(
        'api/v1/feedback/',
        AdaptiveFeedbackView.as_view(),
        name='adaptive_feedback'
    ),

    # AI tutor
    path(
        'api/v1/tutor/chat/',
        AITutorChatView.as_view(),
        name='tutor_chat'
    ),

    # Webhooks
    path(
        'webhooks/ai-engine/',
        AIEngineWebhookView.as_view(),
        name='ai_engine_webhook'
    ),

    # Health check
    path(
        'api/v1/health/',
        health_check,
        name='health_check'
    ),
]
