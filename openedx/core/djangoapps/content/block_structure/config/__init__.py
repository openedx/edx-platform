"""
This module contains various configuration settings via
waffle switches for the Block Structure framework.
"""
from edx_django_utils.cache import RequestCache
from edx_toggles.toggles import WaffleSwitch

from openedx.core.lib.cache_utils import request_cached

from .models import BlockStructureConfiguration

# Switches
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
