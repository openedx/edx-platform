"""
Tests for FeatureProxy
"""

import pytest
import warnings
from django.test import override_settings
from django.utils.functional import empty
from openedx.core.lib.features_setting_proxy import FeaturesProxy


@pytest.fixture
def feature_proxy():
    return FeaturesProxy()


def test_lazy_loading_sets_wrapped(feature_proxy):
    # Tests if the "_wrapped" is empty initially, then invokes _setup method
    # when .get is called, finally checks if "_wrapped" is set(not empty)
    assert getattr(feature_proxy, '_wrapped', empty) is empty
    _ = feature_proxy.get("ANY_SETTING")
    assert getattr(feature_proxy, '_wrapped', empty) is not empty


@override_settings(NEW_FEATURE=True)
def test_getitem_returns_from_django_settings(feature_proxy):
    assert feature_proxy["NEW_FEATURE"] is True


def test_get_returns_default_when_missing(feature_proxy):
    assert feature_proxy.get("NON_EXISTENT") is None
    assert feature_proxy.get("NON_EXISTENT", default="fallback") == "fallback"


def test_getitem_when_key_missing(feature_proxy):
    with pytest.raises(KeyError):
        _ = feature_proxy["NON_EXISTENT"]


@override_settings(MY_FLAG=True)
def test_deleted_flag(settings):
    delattr(settings, 'MY_FLAG')
    with pytest.raises(AttributeError):
        _ = settings.MY_FLAG


@override_settings(ENABLE_XBLOCK=True)
def test_contains_returns_true_if_in_settings(feature_proxy):
    assert "ENABLE_XBLOCK" in feature_proxy


def test_contains_returns_false_if_not_in_settings(feature_proxy):
    assert "NOT_A_SETTING" not in feature_proxy


@override_settings(TEST_KEY_1="VALUE_1", TEST_KEY_2="VALUE_2")
def test_iter_and_len_reflect_all_django_settings(feature_proxy):
    keys = list(iter(feature_proxy))
    assert "TEST_KEY_1" in keys
    # There should be atleast 2 + default django settings
    assert len(feature_proxy) >= 2


@override_settings(TEST_KEY_1="VALUE_1")
def test_items_yields_key_value_pairs(feature_proxy):
    items = dict(feature_proxy.items())
    assert "TEST_KEY_1" in items
    assert items["TEST_KEY_1"] == "VALUE_1"


@override_settings(TEST_KEY_1="VALUE_1")
def test_as_dict_returns_all_settings(feature_proxy):
    settings_dict = feature_proxy.as_dict()
    assert isinstance(settings_dict, dict)
    assert "TEST_KEY_1" in settings_dict


def test_copy_returns_dict(feature_proxy):
    copied = feature_proxy.copy()
    assert isinstance(copied, dict)
    _ = feature_proxy.get("SOME_SETTING")
    assert isinstance(feature_proxy.copy(), dict)


def test_setitem_triggers_deprecation_warning(feature_proxy):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        feature_proxy["NEW_FEATURE"] = False
        assert any("deprecated" in str(warn.message).lower() for warn in w)


def test_delitem_triggers_deprecation_warning(feature_proxy):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        del feature_proxy["NEW_FEATURE"]
        assert any("deprecated" in str(warn.message).lower() for warn in w)


def test_update_triggers_deprecation_warning(feature_proxy):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        feature_proxy.update({"SOME_KEY": True})
        assert any("deprecated" in str(warn.message).lower() for warn in w)
