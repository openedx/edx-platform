"""
Tests for `tahoe_idp_helpers`.
"""
import pytest

from site_config_client.openedx.test_helpers import override_site_config

from openedx.core.djangoapps.site_configuration import tahoe_idp_helpers


@pytest.mark.parametrize('case', [
    {'new_flag': True, 'should_be_enabled': True, 'message': 'new flag should enable it'},
    {'old_flag': True, 'should_be_enabled': True, 'message': 'old legacy flag should enable it'},
    {'global_flag': True, 'should_be_enabled': True, 'message': 'cluster-wide flag should enable it'},
    {'should_be_enabled': False, 'message': 'When no flag is enabled, the feature should be disabled'},
])
def test_is_tahoe_idp_enabled(case, settings, monkeypatch):
    new_flag = case.get('new_flag', False)  # All values default to False, None.
    old_flag = case.get('old_flag', False)
    global_flag = case.get('global_flag', False)

    monkeypatch.setitem(settings.FEATURES, 'ENABLE_TAHOE_IDP', global_flag)
    with override_site_config('admin', ENABLE_TAHOE_IDP=new_flag, ENABLE_TAHOE_IDP=old_flag):
        assert tahoe_idp_helpers.is_tahoe_idp_enabled() == case['should_be_enabled'], case['message']
