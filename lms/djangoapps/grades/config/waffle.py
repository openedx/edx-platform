"""
This module contains various configuration settings via
waffle switches for the Grades app.
"""


from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'grades'

# Switches
ASSUME_ZERO_GRADE_IF_ABSENT = u'assume_zero_grade_if_absent'
DISABLE_REGRADE_ON_POLICY_CHANGE = u'disable_regrade_on_policy_change'

# Course Flags
REJECTED_EXAM_OVERRIDES_GRADE = u'rejected_exam_overrides_grade'
ENFORCE_FREEZE_GRADE_AFTER_COURSE_END = u'enforce_freeze_grade_after_course_end'
WRITABLE_GRADEBOOK = u'writable_gradebook'
BULK_MANAGEMENT = u'bulk_management'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Grades.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Grades: ')


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Grades.
    """
    namespace = WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Grades: ')
    return {
        # By default, enable rejected exam grade overrides. Can be disabled on a course-by-course basis.
        REJECTED_EXAM_OVERRIDES_GRADE: CourseWaffleFlag(
            namespace,
            REJECTED_EXAM_OVERRIDES_GRADE,
            flag_undefined_default=True,
        ),
        ENFORCE_FREEZE_GRADE_AFTER_COURSE_END: CourseWaffleFlag(
            namespace,
            ENFORCE_FREEZE_GRADE_AFTER_COURSE_END,
            flag_undefined_default=True,
        ),
        # Have this course override flag so we can selectively turn off the gradebook for courses.
        WRITABLE_GRADEBOOK: CourseWaffleFlag(
            namespace,
            WRITABLE_GRADEBOOK,
            flag_undefined_default=True,
        ),
        BULK_MANAGEMENT: CourseWaffleFlag(
            namespace,
            BULK_MANAGEMENT,
            flag_undefined_default=False,
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
