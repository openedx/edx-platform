"""
Grade service
"""
from datetime import datetime

from django.contrib.auth import get_user_model
import pytz
from six import text_type

from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.subsection_grade import CreateSubsectionGrade
from lms.djangoapps.utils import _get_key
from opaque_keys.edx.keys import CourseKey, UsageKey
from track.event_transaction_utils import create_new_event_transaction_id, set_event_transaction_type

from .config.waffle import waffle_flags, REJECTED_EXAM_OVERRIDES_GRADE
from .constants import ScoreDatabaseTableEnum, GradeOverrideFeatureEnum
from .events import SUBSECTION_OVERRIDE_EVENT_TYPE
from .models import (
    PersistentSubsectionGrade,
    PersistentSubsectionGradeOverride,
    PersistentSubsectionGradeOverrideHistory
)
from .signals.signals import SUBSECTION_OVERRIDE_CHANGED


USER_MODEL = get_user_model()


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
        usage_key = _get_key(usage_key_or_id, UsageKey)

        # Verify that a corresponding subsection grade exists for the given user and usage_key
        # Raises PersistentSubsectionGrade.DoesNotExist if it does not exist.
        _ = self.get_subsection_grade(user_id, course_key_or_id, usage_key_or_id)

        return PersistentSubsectionGradeOverride.get_override(user_id, usage_key)

    def override_subsection_grade(
            self, user_id, course_key_or_id, usage_key_or_id, earned_all=None, earned_graded=None
    ):
        """
        Creates a PersistentSubsectionGradeOverride corresponding to the given
        user, course, and usage_key.
        Will also create a ``PersistentSubsectionGrade`` for this (user, course, usage_key)
        if none currently exists.

        Fires off a recalculate_subsection_grade async task to update the PersistentCourseGrade table.
        Will not override ``earned_all`` or ``earned_graded`` value if they are ``None``.
        Both of these parameters have ``None`` as their default value.
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        usage_key = _get_key(usage_key_or_id, UsageKey)

        try:
            grade = PersistentSubsectionGrade.read_grade(
                user_id=user_id,
                usage_key=usage_key
            )
        except PersistentSubsectionGrade.DoesNotExist:
            grade = self._create_subsection_grade(user_id, course_key, usage_key)

        override = PersistentSubsectionGradeOverride.update_or_create_override(
            requesting_user=None,
            subsection_grade_model=grade,
            feature=GradeOverrideFeatureEnum.proctoring,
            earned_all_override=earned_all,
            earned_graded_override=earned_graded,
        )

        # Cache a new event id and event type which the signal handler will use to emit a tracking log event.
        create_new_event_transaction_id()
        set_event_transaction_type(SUBSECTION_OVERRIDE_EVENT_TYPE)

        # This will eventually trigger a re-computation of the course grade,
        # taking the new PersistentSubsectionGradeOverride into account.
        SUBSECTION_OVERRIDE_CHANGED.send(
            sender=None,
            user_id=user_id,
            course_id=text_type(course_key),
            usage_id=text_type(usage_key),
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
                feature=GradeOverrideFeatureEnum.proctoring,
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
            course_id=text_type(course_key),
            usage_id=text_type(usage_key),
            only_if_higher=False,
            modified=datetime.now().replace(tzinfo=pytz.UTC),  # Not used when score_deleted=True
            score_deleted=True,
            score_db_table=ScoreDatabaseTableEnum.overrides
        )

    def should_override_grade_on_rejected_exam(self, course_key_or_id):
        """Convienence function to return the state of the CourseWaffleFlag REJECTED_EXAM_OVERRIDES_GRADE"""
        course_key = _get_key(course_key_or_id, CourseKey)
        return waffle_flags()[REJECTED_EXAM_OVERRIDES_GRADE].is_enabled(course_key)

    def _create_subsection_grade(self, user_id, course_key, usage_key):
        """
        Given a user_id, course_key, and subsection usage_key,
        creates a new ``PersistentSubsectionGrade``.
        """
        from djangoapps.courseware.courses import get_course
        course = get_course(course_key, depth=None)
        subsection = course.get_child(usage_key)
        if not subsection:
            raise Exception('Subsection with given usage_key does not exist.')
        user = USER_MODEL.objects.get(id=user_id)
        course_data = CourseData(user, course=course)
        subsection_grade = CreateSubsectionGrade(subsection, course_data.structure, {}, {})
        return subsection_grade.update_or_create_model(user, force_update_subsections=True)
