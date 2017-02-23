"""
This module contains various configuration settings via
waffle switches for the Block Structure framework.
"""

from waffle import switch_is_active


INVALIDATE_CACHE_ON_PUBLISH = u'invalidate_cache_on_publish'
STORAGE_BACKING_FOR_CACHE = u'storage_backing_for_cache'
RAISE_ERROR_WHEN_NOT_FOUND = u'raise_error_when_not_found'


def is_enabled(setting_name):
    """
    Returns whether the given setting is enabled.
    """
    return switch_is_active(
        waffle_switch_name(setting_name)
    )


def waffle_switch_name(setting_name):
    """
    Returns the name of the waffle switch for the
    given name of the setting.
    """
    return u'block_structure.{}'.format(setting_name)
