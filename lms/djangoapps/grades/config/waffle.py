"""
This module contains various configuration settings via
waffle switches for the Grades app.
"""
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace, WaffleFlagNamespace, CourseWaffleFlag

# Namespace
WAFFLE_NAMESPACE = u'grades'

# Switches
ASSUME_ZERO_GRADE_IF_ABSENT = u'assume_zero_grade_if_absent'
DISABLE_REGRADE_ON_POLICY_CHANGE = u'disable_regrade_on_policy_change'

# Course Flags
REJECTED_EXAM_OVERRIDES_GRADE = u'rejected_exam_overrides_grade'


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
            flag_undefined_default=True
        )
    }
