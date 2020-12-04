"""
Waffle flags for instructor dashboard.
"""

from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_NAMESPACE = 'instructor'
# Namespace for instructor waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=WAFFLE_NAMESPACE)

# Waffle flag enable new data download UI on specific course.
# .. toggle_name: instructor.enable_data_download_v2
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: instructor
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-07-8
# .. toggle_target_removal_date: None
# .. toggle_warnings: ??
# .. toggle_tickets: PROD-1309
DATA_DOWNLOAD_V2 = CourseWaffleFlag(
    waffle_namespace=WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix='instructor_dashboard: '),
    flag_name='enable_data_download_v2',
)

# Waffle flag to use optimised is_small_course.
# .. toggle_name: verify_student.optimised_is_small_course
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout to improved is_small_course method.
# .. toggle_category: instructor
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-07-02
# .. toggle_target_removal_date: None
# .. toggle_warnings: n/a
# .. toggle_tickets: PROD-1740
# .. toggle_status: supported
OPTIMISED_IS_SMALL_COURSE = WaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name='optimised_is_small_course',
)


def data_download_v2_is_enabled(course_key):
    """
    check if data download v2 is enabled.
    """
    return DATA_DOWNLOAD_V2.is_enabled(course_key)


def use_optimised_is_small_course():
    return OPTIMISED_IS_SMALL_COURSE.is_enabled()
