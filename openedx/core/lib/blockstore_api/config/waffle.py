"""
Toggles for blockstore.
"""

from edx_toggles.toggles import WaffleSwitch

# .. toggle_name: blockstore.use_blockstore_app_api
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Enable to use the installed blockstore app's Python API directly instead of the
#   external blockstore service REST API.
#   The blockstore REST API is used by default.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2022-01-13
# .. toggle_target_removal_date: None
# .. toggle_tickets: TNL-8705, BD-14
# .. toggle_warning: This temporary feature toggle does not have a target removal date.
BLOCKSTORE_USE_BLOCKSTORE_APP_API = WaffleSwitch(
    'blockstore.use_blockstore_app_api', __name__
)
