"""
Defines grading configuration.
"""


from django.conf import settings

from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag
from lms.djangoapps.grades.config.waffle import ASSUME_ZERO_GRADE_IF_ABSENT


def assume_zero_if_absent(course_key):
    """
    Returns whether an absent grade should be assumed to be zero.
    """
    return (
        should_persist_grades(course_key) and (
            settings.FEATURES.get('ASSUME_ZERO_GRADE_IF_ABSENT_FOR_ALL_TESTS') or
            ASSUME_ZERO_GRADE_IF_ABSENT.is_enabled()
        )
    )


def should_persist_grades(course_key):
    """
    Returns whether grades should be persisted.
    """
    return PersistentGradesEnabledFlag.feature_enabled(course_key)
