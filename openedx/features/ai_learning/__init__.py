"""
AI-Powered Adaptive Learning Integration for Open edX.

This Django application provides the integration layer between Open edX
and the external AI Engine microservices. It handles:

- API endpoints for AI Engine to create/modify courses
- Webhook handlers for student event data
- Configuration and authentication management
- Communication with custom XBlocks
"""

default_app_config = 'openedx.features.ai_learning.apps.AILearningConfig'
