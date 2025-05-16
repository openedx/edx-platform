"""
Configuration for features of Branding
"""
from django.conf import settings
from edx_toggles.toggles import WaffleFlag

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

# Namespace for Waffle flags related to branding
WAFFLE_FLAG_NAMESPACE = "new_catalog_mfe"


def catalog_mfe_enabled():
    """
    Determine if Catalog MFE is enabled, replacing student_dashboard
    """
    return configuration_helpers.get_value(
        'ENABLE_CATALOG_MICROFRONTEND', settings.FEATURES.get('ENABLE_CATALOG_MICROFRONTEND')
    )


# .. toggle_name: new_catalog_mfe.use_new_catalog_page
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Set to True to enable the new catalog page.
# .. toggle_creation_date: 2025-05-15
# .. toggle_target_removal_date: None
# .. toggle_use_cases: open_edx
ENABLE_NEW_CATALOG_PAGE = WaffleFlag(f'{WAFFLE_FLAG_NAMESPACE}.use_new_catalog_page', __name__)


def use_new_catalog_page():
    """
    Returns a boolean if new catalog page should be used.
    """
    return ENABLE_NEW_CATALOG_PAGE.is_enabled()
