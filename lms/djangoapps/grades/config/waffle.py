"""
This module contains various configuration settings via
waffle switches for the Grades app.
"""


from edx_toggles.toggles import LegacyWaffleFlagNamespace, LegacyWaffleSwitch, LegacyWaffleSwitchNamespace

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace
WAFFLE_NAMESPACE = 'grades'

# Switches

# .. toggle_name: grades.assume_zero_grade_if_absent
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: When enabled, an absent grade is assumed to be zero. Alternatively, defining the
#   `settings.FEATURES["ASSUME_ZERO_GRADE_IF_ABSENT_FOR_ALL_TESTS"]` feature flag in the LMS will enable this feature
#   for all courses.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2017-04-11
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/14771
# .. toggle_warnings: This requires the PersistentGradesEnabledFlag to be enabled.
# TODO: Replace with WaffleSwitch(). See waffle_switch(name) docstring.
ASSUME_ZERO_GRADE_IF_ABSENT = 'assume_zero_grade_if_absent'
# .. toggle_name: grades.disable_regrade_on_policy_change
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: When enabled, a change in grading policy will not trigger re-grading.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2017-08-03
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/15733
# TODO: Replace with WaffleSwitch(). See waffle_switch(name) docstring.
DISABLE_REGRADE_ON_POLICY_CHANGE = 'disable_regrade_on_policy_change'

# Course Flags

# .. toggle_name: grades.rejected_exam_overrides_grade
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, a rejected exam will trigger a grade override. Note that this flag is not used
#   in edx-platform, but only in edx-proctoring.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2019-05-29
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/20719
# TODO: Replace with CourseWaffleFlag() from below. See waffle_flag(name) docstring.
REJECTED_EXAM_OVERRIDES_GRADE = 'rejected_exam_overrides_grade'
# .. toggle_name: grades.rejected_exam_overrides_grade
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, grades can no longer be updated 30 days after a course has ended. Note that this
#   is only valid for courses which actually have an end date.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2018-10-01
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/19026
# TODO: Replace with CourseWaffleFlag() from below. See waffle_flag(name) docstring.
ENFORCE_FREEZE_GRADE_AFTER_COURSE_END = 'enforce_freeze_grade_after_course_end'

# .. toggle_name: grades.writable_gradebook
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, add GET/POST endpoints for updating gradebook entries in bulk. Also, a link to
#   the writable gradebook is added to the instructor dashboard.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2018-10-03
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/19054
# .. toggle_warnings: Enabling this requires that the `WRITABLE_GRADEBOOK_URL` setting be properly defined.
# TODO: Replace with CourseWaffleFlag() from below. See waffle_flag(name) docstring.
WRITABLE_GRADEBOOK = 'writable_gradebook'

# .. toggle_name: grades.bulk_management
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, bulk features are visible for management in masters course. As far
#   as we understand, this feature is now unused and obsolete.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2019-08-20
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/21389
# TODO: Replace with CourseWaffleFlag() from below. See waffle_flag(name) docstring.
BULK_MANAGEMENT = 'bulk_management'


def waffle():
    """
    Deprecated: Returns the namespaced, cached, audited Waffle class for Grades.

    Note: Replace uses of this function with direct references to each switch.
      See waffle_switch(name) docstring for details.
    """
    return LegacyWaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix='Grades: ')


def waffle_switch(name):
    """
    Deprecated: Return the corresponding namespaced waffle switch.

    IMPORTANT: Do NOT copy this pattern and do NOT use this to reference new switches.
      Instead, replace the string constants above with the actual switch instances.
      For example::

        ASSUME_ZERO_GRADE_IF_ABSENT = WaffleSwitch(f'{WAFFLE_NAMESPACE}.assume_zero_grade_if_absent')
    """
    return LegacyWaffleSwitch(waffle(), name, module_name=__name__)


def waffle_flags():
    """
    Deprecated: Returns the namespaced, cached, audited Waffle flags dictionary for Grades.

    IMPORTANT: Do NOT copy this pattern and do NOT use this to reference new flags.
      Instead, replace the string constants above with the flag declarations below, and use
      them directly.
    """
    namespace = LegacyWaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix='Grades: ')
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


def gradebook_bulk_management_enabled(course_key):
    """
    Returns whether bulk management features should be specially enabled for a given course.
    """
    return waffle_flags()[BULK_MANAGEMENT].is_enabled(course_key)
