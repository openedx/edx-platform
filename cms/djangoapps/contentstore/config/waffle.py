"""
This module contains various configuration settings via
waffle switches for the contentstore app.
"""


<<<<<<< HEAD
from edx_toggles.toggles import WaffleFlag, WaffleSwitch
=======
from edx_toggles.toggles import WaffleSwitch
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

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

<<<<<<< HEAD
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

=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

# .. toggle_name: studio.custom_relative_dates
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable custom pacing input for Personalized Learner Schedule (PLS).
# ..    This flag guards an input in Studio for a self paced course, where the user can enter date offsets
# ..    for a subsection.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-07-12
# .. toggle_target_removal_date: 2021-12-31
# .. toggle_warning: Flag course_experience.relative_dates should also be active for relative dates functionalities to work.
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-844
CUSTOM_RELATIVE_DATES = CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.custom_relative_dates', __name__)
<<<<<<< HEAD


# .. toggle_name: studio.enable_course_update_notifications
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable course update notifications.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 14-Feb-2024
# .. toggle_target_removal_date: 14-Mar-2024
ENABLE_COURSE_UPDATE_NOTIFICATIONS = CourseWaffleFlag(
    f'{WAFFLE_NAMESPACE}.enable_course_update_notifications',
    __name__
)
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
