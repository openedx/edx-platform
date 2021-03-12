"""Common environment variables unique to the ace_common plugin."""


def plugin_settings(settings):
    """Settings for the ace_common plugin. """

    settings.ACE_ENABLED_CHANNELS = settings.ENV_TOKENS.get('ACE_ENABLED_CHANNELS', settings.ACE_ENABLED_CHANNELS)
    settings.ACE_ENABLED_POLICIES = settings.ENV_TOKENS.get('ACE_ENABLED_POLICIES', settings.ACE_ENABLED_POLICIES)
    settings.ACE_CHANNEL_SAILTHRU_DEBUG = settings.ENV_TOKENS.get(
        'ACE_CHANNEL_SAILTHRU_DEBUG', settings.ACE_CHANNEL_SAILTHRU_DEBUG,
    )
    settings.ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME = settings.ENV_TOKENS.get(
        'ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME', settings.ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME,
    )
    settings.ACE_CHANNEL_SAILTHRU_API_KEY = settings.AUTH_TOKENS.get(
        'ACE_CHANNEL_SAILTHRU_API_KEY', settings.ACE_CHANNEL_SAILTHRU_API_KEY,
    )
    settings.ACE_CHANNEL_SAILTHRU_API_SECRET = settings.AUTH_TOKENS.get(
        'ACE_CHANNEL_SAILTHRU_API_SECRET', settings.ACE_CHANNEL_SAILTHRU_API_SECRET,
    )
    settings.ACE_ROUTING_KEY = settings.ENV_TOKENS.get('ACE_ROUTING_KEY', settings.ACE_ROUTING_KEY)

    settings.ACE_CHANNEL_DEFAULT_EMAIL = settings.ENV_TOKENS.get(
        'ACE_CHANNEL_DEFAULT_EMAIL', settings.ACE_CHANNEL_DEFAULT_EMAIL
    )
    settings.ACE_CHANNEL_TRANSACTIONAL_EMAIL = settings.ENV_TOKENS.get(
        'ACE_CHANNEL_TRANSACTIONAL_EMAIL', settings.ACE_CHANNEL_TRANSACTIONAL_EMAIL
    )
