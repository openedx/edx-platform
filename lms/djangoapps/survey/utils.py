"""
Helper methods for Surveys
"""

from survey.models import SurveyForm, SurveyAnswer
from courseware.access import has_access


def is_survey_required_for_course(course_descriptor):
    """
    Returns whether a Survey is required for this course
    """

    # check to see that the Survey name has been defined in the CourseDescriptor
    # and that the specified Survey exists

    return course_descriptor.course_survey_required and \
        SurveyForm.get(course_descriptor.course_survey_name, throw_if_not_found=False)


def must_answer_survey(course_descriptor, user):
    """
    Returns whether a user needs to answer a required survey
    """
    if not is_survey_required_for_course(course_descriptor):
        return False

    # this will throw exception if not found, but a non existing survey name will
    # be trapped in the above is_survey_required_for_course() method
    survey = SurveyForm.get(course_descriptor.course_survey_name)

    has_staff_access = has_access(user, 'staff', course_descriptor)

    # survey is required and it exists, let's see if user has answered the survey
    # course staff do not need to answer survey
    answered_survey = SurveyAnswer.do_survey_answers_exist(survey, user)
    return not answered_survey and not has_staff_access
