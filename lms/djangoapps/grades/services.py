"""
Grade service
"""
from datetime import datetime

import pytz

from lms.djangoapps.utils import _get_key
from opaque_keys.edx.keys import CourseKey, UsageKey
from track.event_transaction_utils import create_new_event_transaction_id, set_event_transaction_type

from .config.waffle import waffle_flags, REJECTED_EXAM_OVERRIDES_GRADE
from .constants import ScoreDatabaseTableEnum
from .events import SUBSECTION_OVERRIDE_EVENT_TYPE
from .models import (
    PersistentSubsectionGrade,
    PersistentSubsectionGradeOverride,
    PersistentSubsectionGradeOverrideHistory
)
from .signals.signals import SUBSECTION_OVERRIDE_CHANGED


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

        grade = PersistentSubsectionGrade.objects.get(
            user_id=user_id,
            course_id=course_key,
            usage_key=usage_key
        )

        # Create override that will prevent any future updates to grade
        override, _ = PersistentSubsectionGradeOverride.objects.update_or_create(
            grade=grade,
            earned_all_override=earned_all,
            earned_graded_override=earned_graded
        )

        _ = PersistentSubsectionGradeOverrideHistory.objects.create(
            override_id=override.id,
            feature=PersistentSubsectionGradeOverrideHistory.PROCTORING,
            action=PersistentSubsectionGradeOverrideHistory.CREATE_OR_UPDATE
        )

        # Cache a new event id and event type which the signal handler will use to emit a tracking log event.
        create_new_event_transaction_id()
        set_event_transaction_type(SUBSECTION_OVERRIDE_EVENT_TYPE)

        # Signal will trigger subsection recalculation which will call PersistentSubsectionGrade.update_or_create_grade
        # which will use the above override to update the grade before writing to the table.
        SUBSECTION_OVERRIDE_CHANGED.send(
            sender=None,
            user_id=user_id,
            course_id=unicode(course_key),
            usage_id=unicode(usage_key),
            only_if_higher=False,
            modified=override.modified,
            score_deleted=False,
            score_db_table=ScoreDatabaseTableEnum.overrides
        )

    def undo_override_subsection_grade(self, user_id, course_key_or_id, usage_key_or_id):
        """
        Delete the override subsection grade row (the PersistentSubsectionGrade model must already exist)

        Fires off a recalculate_subsection_grade async task to update the PersistentSubsectionGrade table. If the
        override does not exist, no error is raised, it just triggers the recalculation.
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        usage_key = _get_key(usage_key_or_id, UsageKey)

        try:
            override = self.get_subsection_grade_override(user_id, course_key, usage_key)
        except PersistentSubsectionGrade.DoesNotExist:
            return

        # Older rejected exam attempts that transition to verified might not have an override created
        if override is not None:
            _ = PersistentSubsectionGradeOverrideHistory.objects.create(
                override_id=override.id,
                feature=PersistentSubsectionGradeOverrideHistory.PROCTORING,
                action=PersistentSubsectionGradeOverrideHistory.DELETE
            )
            override.delete()

        # Cache a new event id and event type which the signal handler will use to emit a tracking log event.
        create_new_event_transaction_id()
        set_event_transaction_type(SUBSECTION_OVERRIDE_EVENT_TYPE)

        # Signal will trigger subsection recalculation which will call PersistentSubsectionGrade.update_or_create_grade
        # which will no longer use the above deleted override, and instead return the grade to the original score from
        # the actual problem responses before writing to the table.
        SUBSECTION_OVERRIDE_CHANGED.send(
            sender=None,
            user_id=user_id,
            course_id=unicode(course_key),
            usage_id=unicode(usage_key),
            only_if_higher=False,
            modified=datetime.now().replace(tzinfo=pytz.UTC),  # Not used when score_deleted=True
            score_deleted=True,
            score_db_table=ScoreDatabaseTableEnum.overrides
        )

    def should_override_grade_on_rejected_exam(self, course_key_or_id):
        """Convienence function to return the state of the CourseWaffleFlag REJECTED_EXAM_OVERRIDES_GRADE"""
        course_key = _get_key(course_key_or_id, CourseKey)
        return waffle_flags()[REJECTED_EXAM_OVERRIDES_GRADE].is_enabled(course_key)
