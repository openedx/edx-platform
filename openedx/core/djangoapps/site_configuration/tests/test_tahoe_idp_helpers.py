"""
Tests for `tahoe_idp_helpers`.
"""
import pytest

from site_config_client.openedx.test_helpers import override_site_config

from openedx.core.djangoapps.site_configuration import tahoe_idp_helpers


@pytest.mark.parametrize('global_flags,site_flags,should_be_enabled,message', [
    ({}, {'ENABLE_TAHOE_IDP': True}, True, 'site-flag should enable it'),
    ({'ENABLE_TAHOE_IDP': True}, {}, True, 'cluster-wide flag should enable it'),
    ({}, {}, False, 'When no flag is enabled, the feature should be disabled'),
])
def test_is_tahoe_idp_enabled(settings, global_flags, site_flags, should_be_enabled, message):
    settings.FEATURES = global_flags
    with override_site_config('admin', **site_flags):
        assert tahoe_idp_helpers.is_tahoe_idp_enabled() == should_be_enabled, message
