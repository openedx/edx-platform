"""
Toggles for the Agreements app
"""

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


# .. toggle_name: agreements.enable_integrity_signature
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports rollout of the integrity signature feature
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-05-07
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: MST-786

ENABLE_INTEGRITY_SIGNATURE = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    'agreements', 'enable_integrity_signature', __name__,
)


def is_integrity_signature_enabled(course_key):
    if isinstance(course_key, str):
        course_key = CourseKey.from_string(course_key)
    return ENABLE_INTEGRITY_SIGNATURE.is_enabled(course_key)
