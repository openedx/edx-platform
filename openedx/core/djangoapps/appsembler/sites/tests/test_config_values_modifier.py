"""
Tests for TahoeConfigurationValueModifier.
"""
import pytest
from django.contrib.sites.models import Site
from unittest.mock import Mock

from openedx.core.djangoapps.appsembler.sites.config_values_modifier import TahoeConfigurationValueModifier
from openedx.core.djangoapps.appsembler.sites.waffle import ENABLE_CONFIG_VALUES_MODIFIER
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


@pytest.mark.django_db
def test_site_config_init_signal_with_modifier_flag():
    """
    Ensure SiteConfiguration gets a TahoeConfigurationValueModifier instance after initialization.
    """
    with ENABLE_CONFIG_VALUES_MODIFIER.override(True):
        site_config = SiteConfiguration()
    assert site_config.tahoe_config_modifier, (
        'The `init_configuration_modifier_for_site_config` function should be '
        'connected correctly to SiteConfiguration\'s `post_init`'
    )


@pytest.mark.django_db
def test_site_config_init_signal_without_modifier_flag():
    """
    Ensure SiteConfiguration shouldn't get a TahoeConfigurationValueModifier if the waffle flag is disabled.
    """
    with ENABLE_CONFIG_VALUES_MODIFIER.override(False):
        site_config = SiteConfiguration()
    assert not site_config.tahoe_config_modifier, 'ENABLE_CONFIG_VALUES_MODIFIER is disabled, do not init the modifier'


def test_values_normalization():
    """
    Ensure `normalize_get_value_params` normalizes values correctly.
    """
    modifier = TahoeConfigurationValueModifier(site_config_instance=Mock())

    _, lang_code_default = modifier.normalize_get_value_params('LANGUAGE_CODE', None)
    assert lang_code_default == 'en', 'Should always provide LANGUAGE_CODE so them works well'

    platform_name_var, _ = modifier.normalize_get_value_params('PLATFORM_NAME', None)
    assert platform_name_var == 'platform_name', 'Always use lower case `platform_name`'


def test_domain_name():
    modifier = TahoeConfigurationValueModifier(site_config_instance=Mock())
    modifier.site_config_instance.site.domain = 'testing.com'
    assert modifier.get_domain() == 'testing.com'

    modifier.site_config_instance = object()  # An object with no `site` attribute
    assert not modifier.get_domain(), 'Should not get domain when SiteConfiguration instance has no Site'


@pytest.mark.parametrize('config_name, expected_value, message', [
    ['SITE_NAME', 'mysite.com', 'Should sync SITE_NAME with site.domain.'],
    ['LMS_ROOT_URL', 'https://mysite.com', 'Should use `https` for security.'],
    ['ACTIVATION_EMAIL_SUPPORT_LINK', 'https://mysite.com/help', 'Should fix RED-2385.'],
    ['PASSWORD_RESET_SUPPORT_LINK', 'https://mysite.com/help', 'Should fix RED-2471.'],
    ['PASSWORD_RESET_SUPPORT_LINK', 'https://mysite.com/help', 'Should fix RED-2471.'],
])
def test_modifier_urls(settings, config_name, expected_value, message):
    settings.LMS_ROOT_URL = 'https://hello-world.com'
    modifier = TahoeConfigurationValueModifier(site_config_instance=Mock())
    modifier.site_config_instance.site.domain = 'mysite.com'

    should_override, overriding_value = modifier.override_value(config_name)
    assert should_override, 'Should override {}'.format(config_name)
    assert overriding_value == expected_value, message


@pytest.mark.django_db
def test_css_override_file_with_port_number():
    with ENABLE_CONFIG_VALUES_MODIFIER.override(True):
        site_config = SiteConfiguration()
        site_config.site = Site(domain='test.localhost:18000')
    modifier = site_config.tahoe_config_modifier
    assert modifier.get_css_overrides_file() == 'test.localhost.css', 'Should not include port number in css file name'


@pytest.mark.parametrize('config_name', [
    'SITE_NAME',
    'LMS_ROOT_URL',
    'ACTIVATION_EMAIL_SUPPORT_LINK',
    'PASSWORD_RESET_SUPPORT_LINK',
    'css_overrides_file',
])
def test_modifier_urls_no_site(config_name):
    """
    Should not override URls where there is no site on the SiteConfiguration instance.
    """
    modifier = TahoeConfigurationValueModifier(site_config_instance=object())  # An site_config with no `site`
    should_override, _ = modifier.override_value(config_name)
    assert not should_override, 'Do not {} when the SiteConfiguration instance has no site'.format(config_name)


@pytest.mark.parametrize('config_name', [
    'CONTACT_US_ENABLE',
    'CERTIFICATES_HTML_VIEW',
])
def test_non_overriding_values(config_name):
    """
    Should not override values other than explicitly mentioned.
    """
    modifier = TahoeConfigurationValueModifier(site_config_instance=Mock())
    modifier.site_config_instance.site.domain = 'test.localhost:18000'
    should_override, _ = modifier.override_value(config_name)
    assert not should_override, 'Should not override values unless explicitly configured'
