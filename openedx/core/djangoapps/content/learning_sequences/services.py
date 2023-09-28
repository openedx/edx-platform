"""
Learning Sequences Runtime Service
"""


from .api import get_user_course_outline, get_user_course_outline_details


class LearningSequencesRuntimeService:
    """
    Provides functions of the public API as a class injected into edx-proctoring
    """

    def get_user_course_outline_details(self, course_key, user, at_time):
        """
        Returns UserCourseOutlineDetailsData
        """
        return get_user_course_outline_details(course_key, user, at_time)

    def get_user_course_outline(self, course_key, user, at_time):
        """
        Returns UserCourseOutlineData
        """
        return get_user_course_outline(course_key, user, at_time)
