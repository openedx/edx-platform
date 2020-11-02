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

    settings.TAHOE_SILENT_MISSING_CSS_CONFIG = True  # see ./common.py
    settings.TAHOE_TEMP_MONKEYPATCHING_JUNIPER_TESTS = True  # see ./common.py

    if settings.FEATURES.get('APPSEMBLER_MULTI_TENANT_EMAILS', False):
        settings.INSTALLED_APPS += (
            'openedx.core.djangoapps.appsembler.multi_tenant_emails',
        )
