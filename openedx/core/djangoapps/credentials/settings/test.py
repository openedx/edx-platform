"""Test settings for Credentials."""


def plugin_settings(settings):
    # Credentials Settings
    settings.CREDENTIALS_INTERNAL_SERVICE_URL = 'https://credentials-internal.example.com'
    settings.CREDENTIALS_PUBLIC_SERVICE_URL = 'https://credentials.example.com'
