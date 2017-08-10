from datetime import datetime

import logging
import pytz

from opaque_keys.edx.keys import CourseKey, UsageKey
from track.event_transaction_utils import create_new_event_transaction_id, set_event_transaction_type
from util.date_utils import to_timestamp

from .config.waffle import waffle_flags, REJECTED_EXAM_OVERRIDES_GRADE
from .constants import ScoreDatabaseTableEnum
from .models import PersistentSubsectionGrade, PersistentSubsectionGradeOverride
from .signals.signals import SUBSECTION_OVERRIDE_CHANGED

log = logging.getLogger(__name__)


def _get_key(key_or_id, key_cls):
    """
    Helper method to get a course/usage key either from a string or a key_cls,
    where the key_cls (CourseKey or UsageKey) will simply be returned.
    """
    return (
        key_cls.from_string(key_or_id)
        if isinstance(key_or_id, basestring)
        else key_or_id
    )


class GradesService(object):
    """
    Course grade service

    Provides various functions related to getting, setting, and overriding user grades.
    """

    def get_subsection_grade(self, user_id, course_key_or_id, usage_key_or_id):
        """
        Finds and returns the earned subsection grade for user
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        usage_key = _get_key(usage_key_or_id, UsageKey)

        return PersistentSubsectionGrade.objects.get(
            user_id=user_id,
            course_id=course_key,
            usage_key=usage_key
        )

    def get_subsection_grade_override(self, user_id, course_key_or_id, usage_key_or_id):
        """
        Finds the subsection grade for user and returns the override for that grade if it exists

        If override does not exist, returns None. If subsection grade does not exist, will raise an exception.
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        usage_key = _get_key(usage_key_or_id, UsageKey)

        grade = self.get_subsection_grade(user_id, course_key, usage_key)

        try:
            return PersistentSubsectionGradeOverride.objects.get(
                grade=grade
            )
        except PersistentSubsectionGradeOverride.DoesNotExist:
            return None

    def override_subsection_grade(self, user_id, course_key_or_id, usage_key_or_id, earned_all=None,
                                  earned_graded=None):
        """
        Override subsection grade (the PersistentSubsectionGrade model must already exist)

        Fires off a recalculate_subsection_grade async task to update the PersistentSubsectionGrade table. Will not
        override earned_all or earned_graded value if they are None. Both default to None.
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        usage_key = _get_key(usage_key_or_id, UsageKey)

        log.info(
            u"EDUCATOR-1127: Subsection grade override for user {user_id} on subsection {usage_key} in course "
            u"{course_key} would be created with params: {params}"
            .format(
                user_id=unicode(user_id),
                usage_key=unicode(usage_key),
                course_key=unicode(course_key),
                params=unicode({
                    'earned_all': earned_all,
                    'earned_graded': earned_graded,
                })
            )
        )

    def undo_override_subsection_grade(self, user_id, course_key_or_id, usage_key_or_id):
        """
        Delete the override subsection grade row (the PersistentSubsectionGrade model must already exist)

        Fires off a recalculate_subsection_grade async task to update the PersistentSubsectionGrade table. If the
        override does not exist, no error is raised, it just triggers the recalculation.
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        usage_key = _get_key(usage_key_or_id, UsageKey)

        log.info(
            u"EDUCATOR-1127: Subsection grade override for user {user_id} on subsection {usage_key} in course "
            u"{course_key} would be deleted"
            .format(
                user_id=unicode(user_id),
                usage_key=unicode(usage_key),
                course_key=unicode(course_key)
            )
        )

    def should_override_grade_on_rejected_exam(self, course_key_or_id):
        """Convienence function to return the state of the CourseWaffleFlag REJECTED_EXAM_OVERRIDES_GRADE"""
        course_key = _get_key(course_key_or_id, CourseKey)
        return waffle_flags()[REJECTED_EXAM_OVERRIDES_GRADE].is_enabled(course_key)
