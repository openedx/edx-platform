"""
This module contains various configuration settings via
waffle switches for the contentstore app.
"""


from edx_toggles.toggles import WaffleFlag, WaffleSwitch

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace
WAFFLE_NAMESPACE = 'studio'
LOG_PREFIX = 'Studio: '

# Switches
ENABLE_ACCESSIBILITY_POLICY_PAGE = WaffleSwitch(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    f'{WAFFLE_NAMESPACE}.enable_policy_page', __name__
)

# TODO: After removing this flag, add a migration to remove waffle flag in a follow-up deployment.
ENABLE_CHECKLISTS_QUALITY = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    f'{WAFFLE_NAMESPACE}.enable_checklists_quality', __name__, LOG_PREFIX
)

SHOW_REVIEW_RULES_FLAG = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    f'{WAFFLE_NAMESPACE}.show_review_rules', __name__, LOG_PREFIX
)

# Waffle flag to redirect to the library authoring MFE.
# .. toggle_name: contentstore.library_authoring_mfe
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Toggles the new micro-frontend-based implementation of the library authoring experience.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-08-03
# .. toggle_target_removal_date: 2020-12-31
# .. toggle_warning: Also set settings.LIBRARY_AUTHORING_MICROFRONTEND_URL and ENABLE_LIBRARY_AUTHORING_MICROFRONTEND.
# .. toggle_tickets: https://openedx.atlassian.net/wiki/spaces/COMM/pages/1545011241/BD-14+Blockstore+Powered+Content+Libraries+Taxonomies
REDIRECT_TO_LIBRARY_AUTHORING_MICROFRONTEND = WaffleFlag(
    f'{WAFFLE_NAMESPACE}.library_authoring_mfe', __name__, LOG_PREFIX
)
