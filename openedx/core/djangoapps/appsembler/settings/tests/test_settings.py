"""Tests the Appsembler Apps settings modules
"""

import pytest
from mock import patch

from openedx.core.djangoapps.theming.helpers_dirs import Theme

from openedx.core.djangoapps.appsembler.settings.helpers import get_tahoe_theme_static_dirs
from openedx.core.djangoapps.appsembler.settings.settings import (
    devstack_cms,
    devstack_lms,
    production_cms,
    production_lms,
)


@pytest.fixture(scope='function')
def fake_production_settings(settings):
    """
    Pytest fixture to fake production settings such as AUTH_TOKENS that are otherwise missing in tests.
    """
    settings.AUTH_TOKENS = {}
    settings.CELERY_QUEUES = {}
    settings.ALTERNATE_QUEUE_ENVS = []
    settings.INSTALLED_APPS = settings.INSTALLED_APPS.copy()  # Prevent polluting the original list
    settings.FEATURES = settings.FEATURES.copy()  # Prevent polluting other tests.
    settings.ENV_TOKENS = {
        'LMS_BASE': 'fake-lms-base',
        'LMS_ROOT_URL': 'fake-lms-root-url',
        'EMAIL_BACKEND': 'fake-email-backend',
        'FEATURES': {}
    }
    settings.MAIN_SITE_REDIRECT_ALLOWLIST = []
    settings.CELERY_ROUTES = ()
    return settings


def test_devstack_cms(fake_production_settings):
    devstack_cms.plugin_settings(fake_production_settings)


def test_devstack_lms(fake_production_settings):
    devstack_lms.plugin_settings(fake_production_settings)


def test_production_cms(fake_production_settings):
    production_cms.plugin_settings(fake_production_settings)


@pytest.mark.parametrize('retval, additional_count', [(False, 0), (True, 1)])
def test_production_lms(fake_production_settings, retval, additional_count):
    settings = fake_production_settings
    with patch('openedx.core.djangoapps.appsembler.settings.helpers.path.isdir',
               return_value=retval):
        with patch(
            'openedx.core.djangoapps.theming.helpers_dirs.get_themes_unchecked',
            return_value=[Theme('fake-theme', 'fake-theme', '.', '.')]
        ):
            expected_dir_len = len(settings.STATICFILES_DIRS) + additional_count
            production_lms.plugin_settings(settings)
            assert len(settings.STATICFILES_DIRS) == expected_dir_len

    assert settings.FEATURES['TAHOE_SITE_CONFIG_CLIENT_ORGANIZATIONS_SUPPORT'], 'Should be on by default on prod.'


@pytest.fixture(scope='function')
def fake_production_settings_non_comprehensive_themes(settings):
    """
    Pytest fixture to fake production settings for comprehensive theming turned off
    """
    settings.STATICFILES_DIRS = ['dummy', 'dummy']
    settings.ENABLE_COMPREHENSIVE_THEMING = False
    return settings


def test_get_tahoe_theme_static_dirs_non_comprehensive(fake_production_settings_non_comprehensive_themes):
    """
    get_tahoe_theme_static_dirs() should just return the default STATICFILES_DIRS
    when comprehensive theming isn't enabled
    """
    settings = fake_production_settings_non_comprehensive_themes
    assert get_tahoe_theme_static_dirs(settings) == settings.STATICFILES_DIRS
