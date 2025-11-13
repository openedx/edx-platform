"""
Common settings for AI Learning integration.
"""


def plugin_settings(settings):
    """
    Add AI Learning specific settings.
    """
    # AI Engine configuration
    settings.AI_ENGINE_BASE_URL = settings.ENV_TOKENS.get(
        'AI_ENGINE_BASE_URL',
        'http://localhost:8001'
    )

    settings.AI_ENGINE_API_KEY = settings.AUTH_TOKENS.get(
        'AI_ENGINE_API_KEY',
        ''
    )

    settings.AI_ENGINE_TIMEOUT = settings.ENV_TOKENS.get(
        'AI_ENGINE_TIMEOUT',
        30
    )

    # Feature flags
    settings.FEATURES['ENABLE_AI_LEARNING'] = settings.ENV_TOKENS.get(
        'ENABLE_AI_LEARNING',
        False
    )

    settings.FEATURES['ENABLE_AI_TUTOR'] = settings.ENV_TOKENS.get(
        'ENABLE_AI_TUTOR',
        False
    )

    settings.FEATURES['ENABLE_ADAPTIVE_ASSESSMENT'] = settings.ENV_TOKENS.get(
        'ENABLE_ADAPTIVE_ASSESSMENT',
        False
    )

    # LLM Provider configuration
    settings.AI_LLM_PROVIDER = settings.ENV_TOKENS.get(
        'AI_LLM_PROVIDER',
        'gemini'  # Options: 'gemini', 'claude', 'openai'
    )

    settings.AI_LLM_MODEL = settings.ENV_TOKENS.get(
        'AI_LLM_MODEL',
        'gemini-2.0-flash-exp'
    )

    # Rate limiting
    settings.AI_ENGINE_RATE_LIMIT = settings.ENV_TOKENS.get(
        'AI_ENGINE_RATE_LIMIT',
        '100/hour'
    )

    # Webhook configuration
    settings.AI_LEARNING_WEBHOOK_SECRET = settings.AUTH_TOKENS.get(
        'AI_LEARNING_WEBHOOK_SECRET',
        ''
    )
