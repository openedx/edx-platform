from opaque_keys.edx.keys import CourseKey, UsageKey
from lms.djangoapps.grades.models import PersistentSubsectionGrade, PersistentSubsectionGradeOverride


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

        Result is a dict of two key value pairs with keys: earned_all and earned_graded.
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        usage_key = _get_key(usage_key_or_id, UsageKey)

        grade = PersistentSubsectionGrade.objects.get(
            user_id=user_id,
            course_id=course_key,
            usage_key=usage_key
        )
        return {
            'earned_all': grade.earned_all,
            'earned_graded': grade.earned_graded
        }

    def override_subsection_grade(self, user_id, course_key_or_id, usage_key_or_id, earned_all=None,
                                  earned_graded=None):
        """
        Override subsection grade (the PersistentSubsectionGrade model must already exist)

        Will not override earned_all or earned_graded value if they are None. Both default to None.
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        subsection_key = _get_key(usage_key_or_id, UsageKey)

        grade = PersistentSubsectionGrade.objects.get(
            user_id=user_id,
            course_id=course_key,
            usage_key=subsection_key
        )

        # Create override that will prevent any future updates to grade
        PersistentSubsectionGradeOverride.objects.create(
            grade=grade,
            earned_all_override=earned_all,
            earned_graded_override=earned_graded
        )

        # Change the grade as it is now
        if earned_all is not None:
            grade.earned_all = earned_all
        if earned_graded is not None:
            grade.earned_graded = earned_graded
        grade.save()
