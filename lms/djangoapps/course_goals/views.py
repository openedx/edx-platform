""" Course Goal Views """
import json

from django.http import HttpResponse
from django.utils.translation import ugettext as _
from openedx.core.djangolib.markup import Text, HTML
from enum import Enum
from eventtracking import tracker

import api


class CourseGoalOption(Enum):
    """
    Types of goals that a user can select.

    These options are set to a string goal key so that they can be
    referenced elsewhere in the code when necessary. These should not
    be used in user facing code and should never be translated.
    """

    CERTIFY = 'certify'
    COMPLETE = 'complete'
    EXPLORE = 'explore'
    UNSURE = 'unsure'

    @classmethod
    def get_course_goal_keys(self):
        return [key.value for key in self]


def get_goal_text(goal_option):
    """
    This function is used to translate the course goal option into
    a user facing string to be used to represent that particular goal.
    """
    return {
        CourseGoalOption.CERTIFY.value: Text(_('Earn a certificate')),
        CourseGoalOption.COMPLETE.value: Text(_('Complete the course')),
        CourseGoalOption.EXPLORE.value: Text(_('Explore the course')),
        CourseGoalOption.UNSURE.value: Text(_('Not sure yet')),
    }[goal_option]


def set_course_goal(request, course_id, goal_key=None):
    """
    Given a user, a course key and a particular goal, add and save a goal.
    If no goal explicitly given, checks if a goal has been passed as
    a data variable in an ajax call.

    Arguments:
        request (WSGIRequest): the request
        course_id: The id for the course the goal refers to
        goal: An optional value that can also be passed in through the data
            object in an ajax call. This value represents the goal key that maps
            to one of the enumerated goal keys from CourseGoalOption.

    Returns a HTTPResponse including an html stub that can be rendered
    to represent the successful setting of a course goal.
    """
    # If no explicit goal was passed in, try to grab it from the ajax request
    if not goal_key and request.is_ajax():
        goal_key = request.POST.get('goal_key')

    # Create and save course goal
    api.add_course_goal(request.user, course_id, goal_key)

    # Log the event
    tracker.emit(
        'edx.course.goal.added',
        {
            'goal': goal_key,
        }
    )

    # Add a success message
    # TODO: LEARNER-2522: 9/2017: Address success messages later.
    message = ''
    if str(goal_key) == CourseGoalOption.UNSURE.value:
        message = Text(_('No problem, you can add a goal at any point on the sidebar.'))
    elif str(goal_key) == CourseGoalOption.CERTIFY.value:
        message = Text(_("That's great! You can upgrade to verified status in the sidebar."))
    elif str(goal_key) == CourseGoalOption.COMPLETE.value:
        message = Text(_("That's great! If you decide to upgrade to go for a certified status,"
                         " you can upgrade to a verified status in the sidebar."))
    elif str(goal_key) == CourseGoalOption.EXPLORE.value:
        message = Text(_('Sounds great - We hope you enjoy the course!'))

    # Add a dismissible icon to allow user to hide the success message
    html = HTML('{message}<span tabindex="0" class="icon fa fa-times dismiss"></span>').format(message=message)

    if request.is_ajax():
        return HttpResponse(
            json.dumps({
                'html': html
            }),
            content_type="application/json",
        )
