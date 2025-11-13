"""
Django app configuration for AI Learning integration.
"""

from django.apps import AppConfig


class AILearningConfig(AppConfig):
    """
    Configuration for the AI Learning integration app.
    """
    name = 'openedx.features.ai_learning'
    verbose_name = 'AI-Powered Adaptive Learning'

    # Plugin configuration
    plugin_app = {
        'url_config': {
            'lms.djangoapp': {
                'namespace': 'ai_learning',
                'regex': r'^ai-learning/',
                'relative_path': 'urls',
            },
        },
        'settings_config': {
            'lms.djangoapp': {
                'common': {'relative_path': 'settings.common'},
                'production': {'relative_path': 'settings.production'},
            },
        },
    }

    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        from . import signals  # pylint: disable=unused-import,import-outside-toplevel
