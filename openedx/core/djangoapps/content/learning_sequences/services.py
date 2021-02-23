"""
Learning Sequences Runtime Service
"""


from .api.outlines import get_user_course_outline_details


class LearningSequencesRuntimeService(object):
    """
    Provides functions of the public API as a class injected into edx-proctoring
    """

    def get_user_course_outline_details(self, course_key, user, at_time):
        """
        Returns UserCourseOutlineDetailsData
        """
        return get_user_course_outline_details(course_key, user, at_time)
