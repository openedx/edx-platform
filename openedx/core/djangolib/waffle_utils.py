"""
Utilities for waffle usage.
"""
from request_cache.middleware import request_cached
from waffle import switch_is_active


@request_cached
def is_switch_enabled(waffle_name):
    """
    Returns and caches whether the given waffle switch is enabled.
    See testing.waffle_utils.override_config_setting for a
    helper to override and clear the cache during tests.
    """
    return switch_is_active(waffle_name)
