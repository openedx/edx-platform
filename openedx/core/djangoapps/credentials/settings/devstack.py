"""Docker devstack settings for Credentials."""


def plugin_settings(settings):
    # Credentials Settings
    settings.CREDENTIALS_INTERNAL_SERVICE_URL = 'http://edx.devstack.credentials:18150'
    settings.CREDENTIALS_PUBLIC_SERVICE_URL = 'http://localhost:18150'
