"""
This module contains various configuration settings via
waffle switches for the Block Structure framework.
"""
from edx_django_utils.cache import RequestCache
from edx_toggles.toggles.__future__ import WaffleSwitch

from openedx.core.lib.cache_utils import request_cached

from .models import BlockStructureConfiguration

# Switches
INVALIDATE_CACHE_ON_PUBLISH = WaffleSwitch(
    "block_structure.invalidate_cache_on_publish", __name__
)
STORAGE_BACKING_FOR_CACHE = WaffleSwitch(
    "block_structure.storage_backing_for_cache", __name__
)
RAISE_ERROR_WHEN_NOT_FOUND = WaffleSwitch(
    "block_structure.raise_error_when_not_found", __name__
)


def enable_storage_backing_for_cache_in_request():
    """
    Manually override the value of the STORAGE_BACKING_FOR_CACHE switch in the context of the request.
    This function should not be replicated, as it accesses a protected member, and it shouldn't.
    """
    # pylint: disable=protected-access
    STORAGE_BACKING_FOR_CACHE._cached_switches[STORAGE_BACKING_FOR_CACHE.name] = True


@request_cached()
def num_versions_to_keep():
    """
    Returns and caches the current setting for num_versions_to_keep.
    """
    return BlockStructureConfiguration.current().num_versions_to_keep


@request_cached()
def cache_timeout_in_seconds():
    """
    Returns and caches the current setting for cache_timeout_in_seconds.
    """
    return BlockStructureConfiguration.current().cache_timeout_in_seconds
