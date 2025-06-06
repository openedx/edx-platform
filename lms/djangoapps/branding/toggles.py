"""
Configuration for features of Branding
"""
from django.conf import settings
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

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
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Set to True to enable the new catalog page.
# .. toggle_creation_date: 2025-05-15
# .. toggle_target_removal_date: None
# .. toggle_use_cases: open_edx
ENABLE_NEW_CATALOG_PAGE = CourseWaffleFlag(f'{WAFFLE_FLAG_NAMESPACE}.use_new_catalog_page', __name__)
# .. toggle_name: new_catalog_mfe.use_new_course_about_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Set to True to enable the new course about page.
# .. toggle_creation_date: 2025-05-15
# .. toggle_target_removal_date: None
# .. toggle_use_cases: open_edx
ENABLE_NEW_COURSE_ABOUT_PAGE = CourseWaffleFlag(f'{WAFFLE_FLAG_NAMESPACE}.use_new_course_about_page', __name__)
# .. toggle_name: new_catalog_mfe.use_new_index_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Set to True to enable the new index page.
# .. toggle_creation_date: 2025-05-15
# .. toggle_target_removal_date: None
# .. toggle_use_cases: open_edx
ENABLE_NEW_INDEX_PAGE = CourseWaffleFlag(f'{WAFFLE_FLAG_NAMESPACE}.use_new_index_page', __name__)


def use_new_catalog_page(course_key=None):
    """
    Returns a boolean if new catalog page should be used.
    """
    return ENABLE_NEW_CATALOG_PAGE.is_enabled(course_key)


def use_new_course_about_page(course_key=None):
    """
    Returns a boolean if new course about page mfe is enabled.
    """
    return ENABLE_NEW_COURSE_ABOUT_PAGE.is_enabled(course_key)


def use_new_index_page(course_key=None):
    """
    Returns a boolean if new index page mfe is enabled.
    """
    return ENABLE_NEW_INDEX_PAGE.is_enabled(course_key)
