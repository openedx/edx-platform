"""
Production settings for AI Learning integration.
"""


def plugin_settings(settings):
    """
    Production-specific AI Learning settings.
    """
    # Ensure secure connections in production
    if settings.AI_ENGINE_BASE_URL.startswith('http://'):
        raise ValueError(
            'AI_ENGINE_BASE_URL must use HTTPS in production. '
            f'Got: {settings.AI_ENGINE_BASE_URL}'
        )

    # Require API key in production
    if not settings.AI_ENGINE_API_KEY:
        raise ValueError(
            'AI_ENGINE_API_KEY must be set in production'
        )

    # Require webhook secret in production
    if settings.FEATURES.get('ENABLE_AI_LEARNING') and not settings.AI_LEARNING_WEBHOOK_SECRET:
        raise ValueError(
            'AI_LEARNING_WEBHOOK_SECRET must be set when AI Learning is enabled'
        )
