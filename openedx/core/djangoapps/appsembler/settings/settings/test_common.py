"""
Settings for Appsembler on test in both LMS and CMS.
"""
from os import getenv


def plugin_settings(settings):
    """
    Appsembler LMS overrides for testing environment.
    """
    settings.AMC_APP_URL = 'http://localhost:13000'  # Tests needs this URL.
    settings.AMC_APP_OAUTH2_CLIENT_ID = '6f2b93d5c02560c3f93f'  # dummy id

    # Allow enabling the APPSEMBLER_MULTI_TENANT_EMAILS when running unit tests via environment variables,
    # because it's disabled by default.
    settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'] = \
        getenv('TEST_APPSEMBLER_MULTI_TENANT_EMAILS', 'false') == 'true'

    settings.TAHOE_ENABLE_CUSTOM_ERROR_VIEW = False  # see ./common.py
    settings.CUSTOMER_THEMES_BACKEND_OPTIONS = {}

    # Permanently skip some tests that we're unable or don't want to fix
    # yet, this allows us to revisit those tests if needed
    # which is slightly better than just `@skip`
    # usage: decorate the test function or class with: `@skipIf(settings.TAHOE_ALWAYS_SKIP_TEST, '_reason_')`
    settings.TAHOE_ALWAYS_SKIP_TEST = True
    settings.CMS_UPDATE_SEARCH_INDEX_JOB_QUEUE = 'edx.cms.core.default'
    settings.INSTALLED_APPS += [
        'tahoe_sites',  # TODO: Move `tahoe_sites` into `common` settings after rolling out into production.
    ]

    if settings.FEATURES.get('APPSEMBLER_MULTI_TENANT_EMAILS', False):
        settings.INSTALLED_APPS += [
            'openedx.core.djangoapps.appsembler.multi_tenant_emails',
        ]
