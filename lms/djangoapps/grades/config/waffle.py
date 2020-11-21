"""
This module contains various configuration settings via
waffle switches for the Grades app.
"""


from edx_toggles.toggles import WaffleFlagNamespace, WaffleSwitch, WaffleSwitchNamespace
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace
WAFFLE_NAMESPACE = u'grades'

# Switches

# .. toggle_name: grades.assume_zero_grade_if_absent
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: When enabled, an absent grade is assumed to be zero. Alternatively, defining the
#   `settings.FEATURES["ASSUME_ZERO_GRADE_IF_ABSENT_FOR_ALL_TESTS"]` feature flag in the LMS will enable this feature
#   for all courses.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2017-04-11
# .. toggle_target_removal_date: None
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/14771
# .. toggle_warnings: This requires the PersistentGradesEnabledFlag to be enabled.
ASSUME_ZERO_GRADE_IF_ABSENT = u'assume_zero_grade_if_absent'
# .. toggle_name: grades.disable_regrade_on_policy_change
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: When enabled, a change in grading policy will not trigger re-grading.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2017-08-03
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/15733
DISABLE_REGRADE_ON_POLICY_CHANGE = u'disable_regrade_on_policy_change'

# Course Flags

# .. toggle_name: grades.rejected_exam_overrides_grade
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, a rejected exam will trigger a grade override. Note that this flag is not used
#   in edx-platform, but only in edx-proctoring.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2019-05-29
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/20719
REJECTED_EXAM_OVERRIDES_GRADE = u'rejected_exam_overrides_grade'
# .. toggle_name: grades.rejected_exam_overrides_grade
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, grades can no longer be updated 30 days after a course has ended. Note that this
#   is only valid for courses which actually have an end date.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2018-10-01
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/19026
ENFORCE_FREEZE_GRADE_AFTER_COURSE_END = u'enforce_freeze_grade_after_course_end'

# .. toggle_name: grades.writable_gradebook
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, add GET/POST endpoints for updating gradebook entries in bulk. Also, a link to
#   the writable gradebook is added to the instructor dashboard.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2018-10-03
# .. toggle_target_removal_date: None
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/19054
# .. toggle_warnings: Enabling this requires that the `WRITABLE_GRADEBOOK_URL` setting be properly defined.
WRITABLE_GRADEBOOK = u'writable_gradebook'

# .. toggle_name: grades.bulk_management
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, bulk features are visible for management in masters course. As far
#   as we understand, this feature is now unused and obsolete.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2019-08-20
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/21389
BULK_MANAGEMENT = u'bulk_management'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Grades.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Grades: ')


def waffle_switch(name):
    """
    Return the corresponding namespaced waffle switch.

    WARNING: do not replicate this pattern. Instead of declaring waffle switch names as strings, you should create
    WaffleSwitch objects as top-level constants.
    """
    return WaffleSwitch(waffle(), name, module_name=__name__)


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Grades.

    WARNING: do not replicate this pattern. Instead of declaring waffle flag names as strings, you should create
    WaffleFlag and CourseWaffleFlag objects as top-level constants.
    """
    namespace = WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Grades: ')
    return {
        # By default, enable rejected exam grade overrides. Can be disabled on a course-by-course basis.
        # TODO: After removing this flag, add a migration to remove waffle flag in a follow-up deployment.
        REJECTED_EXAM_OVERRIDES_GRADE: CourseWaffleFlag(
            namespace,
            REJECTED_EXAM_OVERRIDES_GRADE,
            __name__,
        ),
        # TODO: After removing this flag, add a migration to remove waffle flag in a follow-up deployment.
        ENFORCE_FREEZE_GRADE_AFTER_COURSE_END: CourseWaffleFlag(
            namespace,
            ENFORCE_FREEZE_GRADE_AFTER_COURSE_END,
            __name__,
        ),
        # Have this course override flag so we can selectively turn off the gradebook for courses.
        # TODO: After removing this flag, add a migration to remove waffle flag in a follow-up deployment.
        WRITABLE_GRADEBOOK: CourseWaffleFlag(
            namespace,
            WRITABLE_GRADEBOOK,
            __name__,
        ),
        BULK_MANAGEMENT: CourseWaffleFlag(
            namespace,
            BULK_MANAGEMENT,
            __name__,
        ),
    }


def is_writable_gradebook_enabled(course_key):
    """
    Returns whether the writable gradebook app is enabled for the given course.
    """
    return waffle_flags()[WRITABLE_GRADEBOOK].is_enabled(course_key)


def gradebook_can_see_bulk_management(course_key):
    """
    Returns whether bulk management features should be visible for the given course.

    (provided that course contains a masters track, as of this writing)
    """
    return waffle_flags()[BULK_MANAGEMENT].is_enabled(course_key)
