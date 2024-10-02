"""Common environment variables unique to the ace_common plugin."""
from openedx.core.djangoapps.ace_common.utils import setup_firebase_app


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
    settings.FCM_APP_NAME = settings.ENV_TOKENS.get('FCM_APP_NAME', settings.FCM_APP_NAME)
    settings.FIREBASE_CREDENTIALS_PATH = settings.ENV_TOKENS.get(
        'FIREBASE_CREDENTIALS_PATH', settings.FIREBASE_CREDENTIALS_PATH
    )
    settings.FIREBASE_CREDENTIALS = settings.ENV_TOKENS.get('FIREBASE_CREDENTIALS', settings.FIREBASE_CREDENTIALS)

    settings.FIREBASE_APP = setup_firebase_app(
        settings.FIREBASE_CREDENTIALS_PATH or settings.FIREBASE_CREDENTIALS, settings.FCM_APP_NAME
    )
    if settings.FIREBASE_APP:
        settings.ACE_ENABLED_CHANNELS.append(settings.ACE_CHANNEL_DEFAULT_PUSH)
        settings.ACE_ENABLED_POLICIES.append('course_push_notification_optout')

        settings.PUSH_NOTIFICATIONS_SETTINGS = {
            'CONFIG': 'push_notifications.conf.AppConfig',
            'APPLICATIONS': {
                settings.FCM_APP_NAME: {
                    'PLATFORM': 'FCM',
                    'FIREBASE_APP': settings.FIREBASE_APP,
                },
            },
            'UPDATE_ON_DUPLICATE_REG_ID': True,
        }
