"""
Helper methods for Surveys
"""

from survey.models import SurveyForm, SurveyAnswer

def is_survey_required_for_course(course_descriptor):
    """
    Returns whether a Survey is required for this course
    """

    # check to see that the Survey name has been defined in the CourseDescriptor
    # and that the specified Survey exists

    return course_descriptor.course_survey_required and \
        SurveyForm.get(course_descriptor.course_survey_name, throw_if_not_found=False)


def has_user_answered_required_survey_for_course(course_descriptor, user):
    """
    Returns whether a user needs to answer a required course
    """

    if not is_survey_required_for_course(course_descriptor):
        return False

    survey = SurveyForm.get(course_descriptor.course_survey_name, throw_if_not_found=False)
    if not survey:
        return False

    # survey is required and it exists, let's see if user has answered the survey
    return SurveyAnswer.do_survey_answers_exist(survey, user)
