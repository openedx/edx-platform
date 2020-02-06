"""
Toggles for courseware in-course experience.
"""

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace

# Namespace for courseware waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='courseware')

# Waffle flag to redirect to another learner profile experience.
# .. toggle_name: courseware.redirect_to_microfrontend
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout of a new micro-frontend-based implementation of the courseware page.
# .. toggle_category: micro-frontend
# .. toggle_use_cases: incremental_release, open_edx
# .. toggle_creation_date: 2020-01-29
# .. toggle_expiration_date: 2020-12-31
# .. toggle_warnings: Also set settings.LEARNING_MICROFRONTEND_URL and ENABLE_COURSEWARE_MICROFRONTEND.
# .. toggle_tickets: TNL-6982
# .. toggle_status: supported
REDIRECT_TO_COURSEWARE_MICROFRONTEND = CourseWaffleFlag(WAFFLE_FLAG_NAMESPACE, 'redirect_to_microfrontend')


def should_redirect_to_courseware_microfrontend(course_key):
    return (
        configuration_helpers.get_value('ENABLE_COURSEWARE_MICROFRONTEND') and
        REDIRECT_TO_COURSEWARE_MICROFRONTEND.is_enabled(course_key)
    )
