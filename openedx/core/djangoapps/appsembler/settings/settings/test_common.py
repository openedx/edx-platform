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

    # TODO: Remove when AMC is removed: RED-2845
    settings.FEATURES['TAHOE_SITES_USE_ORGS_MODELS'] = getenv('TEST_TAHOE_SITES_USE_ORGS_MODELS', 'true') == 'true'

    if getenv('TEST_ENABLE_TIERS_APP', 'false') == 'true':
        settings.INSTALLED_APPS += [
            'tiers',
        ]

    if settings.FEATURES.get('APPSEMBLER_MULTI_TENANT_EMAILS', False):
        settings.INSTALLED_APPS += [
            'openedx.core.djangoapps.appsembler.multi_tenant_emails',
        ]

    settings.CACHES.update({
        'tahoe_userprofile_metadata_cache': {
            'KEY_PREFIX': 'tahoe_userprofile_metadata',
            'LOCATION': 'edx_loc_mem_cache',
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
