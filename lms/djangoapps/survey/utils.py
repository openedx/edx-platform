"""
Helper methods for Surveys
"""


def is_survey_required_for_course(course_descriptor):
    """
    Returns whether a Survey is required for this course
    """

    # check to see that the Survey name has been defined in the CourseDescriptor

    return False

def show_user_required_survey_for_course(course_descriptor, user):
    """
    Returns whether a user needs to answer a required course
    """

    if not is_survey_required_for_course(course_descriptor):
        return False

    # survey is required, let's see if user has answered the survey
    return False
