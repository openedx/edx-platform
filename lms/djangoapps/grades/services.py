from datetime import datetime

import pytz

from opaque_keys.edx.keys import CourseKey, UsageKey
from track.event_transaction_utils import create_new_event_transaction_id, set_event_transaction_type
from util.date_utils import to_timestamp

from .constants import ScoreDatabaseTableEnum
from .models import PersistentSubsectionGrade, PersistentSubsectionGradeOverride
from .signals.handlers import SUBSECTION_RESCORE_EVENT_TYPE


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
        from .tasks import recalculate_subsection_grade_v3  # prevent circular import

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

        # Recalculation will call PersistentSubsectionGrade.update_or_create_grade which will use the above override
        # to update the grade before writing to the table.
        event_transaction_id = create_new_event_transaction_id()
        set_event_transaction_type(SUBSECTION_RESCORE_EVENT_TYPE)
        recalculate_subsection_grade_v3.apply_async(
            kwargs=dict(
                user_id=user_id,
                course_id=unicode(course_key),
                usage_id=unicode(usage_key),
                only_if_higher=False,
                expected_modified=to_timestamp(override.modified),
                event_transaction_id=unicode(event_transaction_id),
                event_transaction_type=SUBSECTION_RESCORE_EVENT_TYPE,
                score_db_table=ScoreDatabaseTableEnum.overrides
            )
        )

    def undo_override_subsection_grade(self, user_id, course_key_or_id, usage_key_or_id):
        """
        Delete the override subsection grade row (the PersistentSubsectionGrade model must already exist)

        Fires off a recalculate_subsection_grade async task to update the PersistentSubsectionGrade table. If the
        override does not exist, no error is raised, it just triggers the recalculation.
        """
        from .tasks import recalculate_subsection_grade_v3  # prevent circular import

        course_key = _get_key(course_key_or_id, CourseKey)
        usage_key = _get_key(usage_key_or_id, UsageKey)

        override = self.get_subsection_grade_override(user_id, course_key, usage_key)
        # Older rejected exam attempts that transition to verified might not have an override created
        if override is not None:
            override.delete()

        event_transaction_id = create_new_event_transaction_id()
        set_event_transaction_type(SUBSECTION_RESCORE_EVENT_TYPE)
        recalculate_subsection_grade_v3.apply_async(
            kwargs=dict(
                user_id=user_id,
                course_id=unicode(course_key),
                usage_id=unicode(usage_key),
                only_if_higher=False,
                # Not used when score_deleted=True:
                expected_modified=to_timestamp(datetime.now().replace(tzinfo=pytz.UTC)),
                score_deleted=True,
                event_transaction_id=unicode(event_transaction_id),
                event_transaction_type=SUBSECTION_RESCORE_EVENT_TYPE,
                score_db_table=ScoreDatabaseTableEnum.overrides
            )
        )
