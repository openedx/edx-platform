"""
This module contains various configuration settings via
waffle switches for the Block Structure framework.
"""
import logging

from openedx.core.djangolib.waffle_utils import is_switch_enabled
from request_cache.middleware import request_cached, RequestCache, func_call_cache_key

from .models import BlockStructureConfiguration


log = logging.getLogger(__name__)


INVALIDATE_CACHE_ON_PUBLISH = u'invalidate_cache_on_publish'
STORAGE_BACKING_FOR_CACHE = u'storage_backing_for_cache'
RAISE_ERROR_WHEN_NOT_FOUND = u'raise_error_when_not_found'
PRUNE_OLD_VERSIONS = u'prune_old_versions'


def is_enabled(setting_name):
    """
    Returns whether the given block_structure setting
    is enabled.
    """
    bs_waffle_name = _bs_waffle_switch_name(setting_name)
    return is_switch_enabled(bs_waffle_name)


def enable_for_current_request(setting_name):
    """
    Enables the given block_structure setting for the
    duration of the current request.
    """
    cache_key = func_call_cache_key(
        is_switch_enabled.request_cached_contained_func,
        _bs_waffle_switch_name(setting_name),
    )
    RequestCache.get_request_cache().data[cache_key] = True
    log.warning(u'BlockStructure: Config %s is enabled for current request.', setting_name)


@request_cached
def num_versions_to_keep():
    """
    Returns and caches the current setting for num_versions_to_keep.
    """
    return BlockStructureConfiguration.current().num_versions_to_keep


@request_cached
def cache_timeout_in_seconds():
    """
    Returns and caches the current setting for cache_timeout_in_seconds.
    """
    return BlockStructureConfiguration.current().cache_timeout_in_seconds


def _bs_waffle_switch_name(setting_name):
    """
    Returns the name of the waffle switch for the
    given block structure setting.
    """
    return u'block_structure.{}'.format(setting_name)
