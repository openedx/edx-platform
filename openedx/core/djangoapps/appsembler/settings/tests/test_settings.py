"""Tests the Appsembler Apps settings modules
"""

import pytest
from mock import patch
from path import Path

from openedx.core.djangoapps.theming.helpers_dirs import Theme

from openedx.core.djangoapps.appsembler.settings.settings import (
    devstack_cms,
    devstack_lms,
    production_cms,
    production_lms,
)


class FakeSettings:
    pass


def get_faked_settings():
    settings = FakeSettings()

    settings.INSTALLED_APPS = []
    settings.FEATURES = {}
    settings.AMC_APP_URL = ''
    settings.AMC_APP_OAUTH2_CLIENT_ID = ''
    settings.APPSEMBLER_FEATURES = {}
    settings.MIDDLEWARE = [
        'django.contrib.sites.middleware.CurrentSiteMiddleware',
    ]
    settings.STATICFILES_DIRS = []
    settings.CACHES = {}
    settings.ENABLE_COMPREHENSIVE_THEMING = True
    settings.PROJECT_ROOT = Path('/tmp/')

    settings.AUTH_TOKENS = {}
    settings.QUEUE_VARIANT = 'fake-queue-variant'
    settings.CELERY_QUEUES = {}
    settings.ALTERNATE_QUEUE_ENVS = []
    settings.ENV_TOKENS = {
        'LMS_BASE': 'fake-lms-base',
        'LMS_ROOT_URL': 'fake-lms-root-url',
        'EMAIL_BACKEND': 'fake-email-backend',
        'FEATURES': {}
    }
    settings.COMPREHENSIVE_THEME_DIRS = ['/path/to/nowhere']
    settings.MAIN_SITE_REDIRECT_WHITELIST = []
    return settings


def test_devstack_cms():
    settings = get_faked_settings()
    devstack_cms.plugin_settings(settings)


def test_devstack_lms():
    settings = get_faked_settings()
    devstack_lms.plugin_settings(settings)


def test_production_cms():
    settings = get_faked_settings()
    production_cms.plugin_settings(settings)


@pytest.mark.parametrize('retval, additional_count', [(False, 0), (True, 1)])
def test_production_lms(retval, additional_count):
    settings = get_faked_settings()
    with patch('openedx.core.djangoapps.appsembler.settings.settings.production_lms.path.isdir',
               return_value=retval):
        with patch(
            'openedx.core.djangoapps.theming.helpers_dirs.get_themes_unchecked',
            return_value=[Theme('fake-theme', 'fake-theme', '.', '.')]
        ):
            expected_dir_len = len(settings.STATICFILES_DIRS) + additional_count
            production_lms.plugin_settings(settings)
            assert len(settings.STATICFILES_DIRS) == expected_dir_len
