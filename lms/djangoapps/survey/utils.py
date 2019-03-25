"""
Utilities for determining whether or not a survey needs to be completed.
"""
from courseware.access import has_access
from survey.models import SurveyForm, SurveyAnswer


def is_survey_required_for_course(course_descriptor):
    """
    Returns whether a Survey is required for this course
    """

    # Check to see that the survey is required in the CourseDescriptor.
    if not getattr(course_descriptor, 'course_survey_required', False):
        return False

    # Check that the specified Survey for the course exists.
    return SurveyForm.get(course_descriptor.course_survey_name, throw_if_not_found=False)


def is_survey_required_and_unanswered(user, course_descriptor):
    """
    Returns whether a user is required to answer the survey and has yet to do so.
    """

    if not is_survey_required_for_course(course_descriptor):
        return False

    # anonymous users do not need to answer the survey
    if user.is_anonymous:
        return False

    # course staff do not need to answer survey
    has_staff_access = has_access(user, 'staff', course_descriptor)
    if has_staff_access:
        return False

    # survey is required and it exists, let's see if user has answered the survey
    survey = SurveyForm.get(course_descriptor.course_survey_name)
    answered_survey = SurveyAnswer.do_survey_answers_exist(survey, user)
    if not answered_survey:
        return True
