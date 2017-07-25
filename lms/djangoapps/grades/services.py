from lms.djangoapps.grades.models import PersistentSubsectionGrade, PersistentSubsectionGradeOverride


class GradesService(object):
    """
    Course grade service

    Provides various functions related to getting, setting, and overriding user grades.
    """

    def get_subsection_grade(self, user_id, course_key_or_id, subsection):
        """
        Finds and returns the earned subsection grade for user

        Result is a dict of two key value pairs with keys: earned_all and earned_graded.
        """
        grade = PersistentSubsectionGrade.objects.get(
            user_id=user_id,
            course_id=course_key_or_id,
            usage_key=subsection
        )
        return {
            'earned_all': grade.earned_all,
            'earned_graded': grade.earned_graded
        }

    def override_subsection_grade(self, user_id, course_key_or_id, subsection, earned_all=None, earned_graded=None):
        """
        Override subsection grade (the PersistentSubsectionGrade model must already exist)

        Will not override earned_all or earned_graded value if they are None. Both default to None.
        """
        grade = PersistentSubsectionGrade.objects.get(
            user_id=user_id,
            course_id=course_key_or_id,
            usage_key=subsection
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
