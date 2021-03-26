"""
Grade service
"""


from . import api


class GradesService:
    """
    Course grade service

    Provides various functions related to getting, setting, and overriding user grades.
    """

    def get_subsection_grade(self, user_id, course_key_or_id, usage_key_or_id):
        """
        Finds and returns the earned subsection grade for user
        """
        return api.get_subsection_grade(user_id, course_key_or_id, usage_key_or_id)

    def get_subsection_grade_override(self, user_id, course_key_or_id, usage_key_or_id):
        """
        Finds the subsection grade for user and returns the override for that grade if it exists

        If override does not exist, returns None. If subsection grade does not exist, will raise an exception.
        """
        return api.get_subsection_grade_override(user_id, course_key_or_id, usage_key_or_id)

    def override_subsection_grade(
            self, user_id, course_key_or_id, usage_key_or_id, earned_all=None, earned_graded=None,
            feature=api.constants.GradeOverrideFeatureEnum.proctoring, overrider=None, comment=None
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
        return api.override_subsection_grade(user_id,
                                             course_key_or_id,
                                             usage_key_or_id,
                                             earned_all=earned_all,
                                             earned_graded=earned_graded,
                                             feature=feature,
                                             overrider=overrider,
                                             comment=comment)

    def undo_override_subsection_grade(self, user_id, course_key_or_id, usage_key_or_id,
                                       feature=api.constants.GradeOverrideFeatureEnum.proctoring):
        """
        Delete the override subsection grade row (the PersistentSubsectionGrade model must already exist)

        Fires off a recalculate_subsection_grade async task to update the PersistentSubsectionGrade table. If the
        override does not exist, no error is raised, it just triggers the recalculation.
        """
        return api.undo_override_subsection_grade(user_id, course_key_or_id, usage_key_or_id, feature=feature)

    def should_override_grade_on_rejected_exam(self, course_key_or_id):
        """Convenience function to return the state of the CourseWaffleFlag REJECTED_EXAM_OVERRIDES_GRADE"""
        return api.should_override_grade_on_rejected_exam(course_key_or_id)
