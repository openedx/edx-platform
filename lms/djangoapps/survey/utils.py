"""
Utilities for determining whether or not a survey needs to be completed.
"""

from django.utils.translation import ugettext as _

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.access_response import AccessError
from lms.djangoapps.courseware.access_utils import ACCESS_GRANTED
from lms.djangoapps.survey.models import SurveyAnswer, SurveyForm


class SurveyRequiredAccessError(AccessError):
    """
    Access denied because the user has not completed a required survey
    """
    def __init__(self):
        error_code = "survey_required"
        developer_message = u"User must complete a survey"
        user_message = _(u"You must complete a survey")
        super(SurveyRequiredAccessError, self).__init__(error_code, developer_message, user_message)


def is_survey_required_for_course(course_descriptor):
    """
    Returns whether a Survey is required for this course
    """

    # Check to see that the survey is required in the CourseDescriptor.
    if not getattr(course_descriptor, 'course_survey_required', False):
        return SurveyRequiredAccessError()

    # Check that the specified Survey for the course exists.
    return SurveyForm.get(course_descriptor.course_survey_name, throw_if_not_found=False)


def check_survey_required_and_unanswered(user, course_descriptor):
    """
    Checks whether a user is required to answer the survey and has yet to do so.

    Returns:
        AccessResponse: Either ACCESS_GRANTED or SurveyRequiredAccessError.
    """

    if not is_survey_required_for_course(course_descriptor):
        return ACCESS_GRANTED

    # anonymous users do not need to answer the survey
    if user.is_anonymous:
        return ACCESS_GRANTED

    # course staff do not need to answer survey
    has_staff_access = has_access(user, 'staff', course_descriptor)
    if has_staff_access:
        return ACCESS_GRANTED

    # survey is required and it exists, let's see if user has answered the survey
    survey = SurveyForm.get(course_descriptor.course_survey_name)
    answered_survey = SurveyAnswer.do_survey_answers_exist(survey, user)
    if answered_survey:
        return ACCESS_GRANTED

    return SurveyRequiredAccessError()
