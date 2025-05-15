"""
Configuration for features of Branding
"""
from edx_toggles.toggles import WaffleFlag


# Namespace for Waffle flags related to branding
WAFFLE_FLAG_NAMESPACE = "new_catalog_mfe"

# .. toggle_name: new_catalog_mfe.use_new_index_page
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Set to True to enable the new index page.
# .. toggle_creation_date: 2025-05-15
# .. toggle_target_removal_date: None
# .. toggle_use_cases: open_edx
ENABLE_NEW_INDEX_PAGE = WaffleFlag(f'{WAFFLE_FLAG_NAMESPACE}.use_new_index_page', __name__)


def use_new_index_page():
    """
    Returns a boolean if new index page mfe is enabled.
    """
    return ENABLE_NEW_INDEX_PAGE.is_enabled()
