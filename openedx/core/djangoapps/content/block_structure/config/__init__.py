"""
This module contains various configuration settings via
waffle switches for the Block Structure framework.
"""
from edx_django_utils.cache import RequestCache
from edx_toggles.toggles import WaffleSwitch

from openedx.core.lib.cache_utils import request_cached

from .models import BlockStructureConfiguration

# Switches
# .. toggle_name: block_structure.invalidate_cache_on_publish
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: When enabled, the block structure cache is invalidated when changes to
#   courses are published. If `block_structure.storage_backing_for_cache` is active, all block
#   structures related to the published course are also cleared from storage.
# .. toggle_warning: This switch will likely be deprecated and removed.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2017-02-23
# .. toggle_target_removal_date: 2017-05-23
# .. toggle_tickets: https://github.com/openedx/edx-platform/pull/14358,
#   https://github.com/openedx/edx-platform/pull/14571,
#   https://openedx.atlassian.net/browse/DEPR-144
INVALIDATE_CACHE_ON_PUBLISH = WaffleSwitch(
    "block_structure.invalidate_cache_on_publish", __name__
)

# .. toggle_name: block_structure.storage_backing_for_cache
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: When enabled, block structures are stored in a more permanent storage,
#   like a database, which provides an additional backup for cache misses, instead having them
#   regenerated. The regenration of block structures is a time consuming process. Therefore,
#   enabling this switch is recommended for Production.
# .. toggle_warning: Depends on `BLOCK_STRUCTURES_SETTINGS['STORAGE_CLASS']` and
#   `BLOCK_STRUCTURES_SETTINGS['STORAGE_KWARGS']`.
#   This switch will likely be deprecated and removed.
#   The annotation will be updated with the DEPR ticket once that process has started.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2017-02-23
# .. toggle_target_removal_date: 2017-05-23
# .. toggle_tickets: https://github.com/openedx/edx-platform/pull/14512,
#   https://github.com/openedx/edx-platform/pull/14770,
#   https://openedx.atlassian.net/browse/DEPR-145
STORAGE_BACKING_FOR_CACHE = WaffleSwitch(
    "block_structure.storage_backing_for_cache", __name__
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
