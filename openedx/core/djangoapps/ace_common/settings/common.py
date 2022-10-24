"""
Settings for ace_common app.
"""

ACE_ROUTING_KEY = 'edx.lms.core.default'


def plugin_settings(settings):  # lint-amnesty, pylint: disable=missing-function-docstring, missing-module-docstring
    settings.ACE_ENABLED_CHANNELS = [
        'django_email'
    ]
    settings.ACE_ENABLED_POLICIES = [
        'bulk_email_optout'
    ]
    settings.ACE_CHANNEL_SAILTHRU_DEBUG = True
    settings.ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME = 'Automated Communication Engine Email'
    settings.ACE_CHANNEL_SAILTHRU_API_KEY = None
    settings.ACE_CHANNEL_SAILTHRU_API_SECRET = None
    settings.ACE_CHANNEL_DEFAULT_EMAIL = 'django_email'
    settings.ACE_CHANNEL_TRANSACTIONAL_EMAIL = 'django_email'

    settings.ACE_ROUTING_KEY = ACE_ROUTING_KEY

    settings.FEATURES['test_django_plugin'] = True
