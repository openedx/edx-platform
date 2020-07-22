"""
Settings for Appsembler on test in both LMS and CMS.
"""
from os import getenv


def plugin_settings(settings):
    """
    Appsembler LMS overrides for testing environment.
    """
    settings.USE_S3_FOR_CUSTOMER_THEMES = False

    settings.AMC_APP_URL = 'http://localhost:13000'  # Tests needs this URL.

    # Allow enabling the APPSEMBLER_MULTI_TENANT_EMAILS when running unit tests via environment variables,
    # because it's disabled by default.
    settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'] = \
        getenv('TEST_APPSEMBLER_MULTI_TENANT_EMAILS', 'false') == 'true'

    if settings.FEATURES.get('APPSEMBLER_MULTI_TENANT_EMAILS', False):
        settings.INSTALLED_APPS += (
            'openedx.core.djangoapps.appsembler.multi_tenant_emails',
        )
