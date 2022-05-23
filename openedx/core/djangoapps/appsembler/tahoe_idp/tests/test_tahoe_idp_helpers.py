"""
Tests for `tahoe_idp.helpers`.
"""
from unittest.mock import patch, Mock

import pytest

from site_config_client.openedx.test_helpers import override_site_config

from openedx.core.djangoapps.appsembler.tahoe_idp import helpers


@pytest.mark.parametrize('global_flags,site_flags,should_be_enabled,message', [
    ({}, {'ENABLE_TAHOE_IDP': True}, True, 'site-flag should enable it'),
    ({'ENABLE_TAHOE_IDP': True}, {}, True, 'cluster-wide flag should enable it'),
    ({}, {}, False, 'When no flag is enabled, the feature should be disabled'),
])
def test_is_tahoe_idp_enabled(settings, global_flags, site_flags, should_be_enabled, message):
    settings.FEATURES = global_flags
    with override_site_config('admin', **site_flags):
        assert helpers.is_tahoe_idp_enabled() == should_be_enabled, message


def test_idp_login_url():
    """
    Tests for `get_idp_login_url`.
    """
    assert helpers.get_idp_login_url() == '/auth/login/tahoe-idp/?auth_entry=login'


def test_idp_login_url_with_next_url():
    """
    Tests for `get_idp_login_url` with next URL.
    """
    url = helpers.get_idp_login_url(next_url='/dashboard?&page=1')
    assert url == '/auth/login/tahoe-idp/?auth_entry=login&next=%2Fdashboard%3F%26page%3D1', 'should encode `next`'


def test_get_idp_register_url():
    url = helpers.get_idp_register_url()
    assert url == '/register-use-fa-form'


def test_get_idp_register_url_with_next():
    url = helpers.get_idp_register_url(next_url='/courses?per_page=10')
    assert url == '/register-use-fa-form?next=%2Fcourses%3Fper_page%3D10', 'should add encoded `next`'


def test_get_idp_form_url_with_tahoe_idp_disabled(settings):
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': True}
    with override_site_config('admin', ENABLE_TAHOE_IDP=False):
        assert not helpers.get_idp_form_url(Mock(), Mock(), Mock()), 'Only get a redirect URL when `tahoe-idp` is used'


def test_get_idp_form_url_with_tahoe_tpa_disabled(settings):
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': False}
    with override_site_config('admin', ENABLE_TAHOE_IDP=True):
        url = helpers.get_idp_form_url(Mock(), Mock(), Mock())

    assert not url, 'Only get a redirect URL when Third Party Auth is used'


def test_get_idp_form_url_for_login(settings):
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': True}
    with override_site_config('admin', ENABLE_TAHOE_IDP=True):
        url = helpers.get_idp_form_url(Mock(), 'login', '/home')

    assert url == '/auth/login/tahoe-idp/?auth_entry=login&next=%2Fhome'


@patch('openedx.core.djangoapps.appsembler.tahoe_idp.helpers.pipeline_running', Mock(return_value=False))
def test_get_idp_form_url_for_register_without_pipeline(settings):
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': True}

    with override_site_config('admin', ENABLE_TAHOE_IDP=True):
        url = helpers.get_idp_form_url(None, 'register', '/home')

    assert url == '/register-use-fa-form?next=%2Fhome', 'Return a URL when there is no running pipeline'


@patch('openedx.core.djangoapps.appsembler.tahoe_idp.helpers.pipeline_running', Mock(return_value=True))
def test_get_idp_form_url_for_register_with_pipeline(settings):
    """
    A running pipeline means a user already coming from Third Party Auth.

    Upon registration, Open edX  auto-submits the frontend hidden registration form.
    Returning, None to avoid breaking an otherwise needed form submit.
    """
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': True}
    with override_site_config('admin', ENABLE_TAHOE_IDP=True):
        url = helpers.get_idp_form_url(None, 'register', '/home')
    assert not url, 'Return no URL when there is a running pipeline'
