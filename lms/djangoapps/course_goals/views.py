"""
Helper functions that handle the creating, updating and deleting of course goals.
"""
import json

from django.http import HttpResponse
from django.utils.translation import ugettext as _
from openedx.core.djangolib.markup import Text, HTML
from enum import Enum
from eventtracking import tracker

from .models import CourseGoal
from opaque_keys.edx.keys import CourseKey


class CourseGoalType(Enum):
    """
    Types of goals that a user can select.
    """
    CERTIFY = 'certify'
    COMPLETE = 'complete'
    EXPLORE = 'explore'
    UNSURE = 'unsure'


def get_course_goal_options():
    return [CourseGoalType.CERTIFY.value, CourseGoalType.COMPLETE.value,
            CourseGoalType.EXPLORE.value, CourseGoalType.UNSURE.value]


def set_course_goal(request, course_id, goal=None):
    """
    Given a user, a course key and a particular goal, add and save a goal.
    If no goal explicitly given, checks if a goal has been passed as
    a data variable in an ajax call.
    """
    # If no explicit goal was passed in, try to grab it from the ajax request
    if not goal and request.is_ajax():
        goal = request.POST.get('goal')

    # First ensure that the goal is an acceptable choice
    if goal not in get_course_goal_options():
        raise KeyError()

    # Remove the existing course goal for the user
    remove_course_goal(request.user, course_id)

    # Create and save course goal
    add_course_goal(request.user, course_id, goal)

    # Log the event
    tracker.emit(
        'edx.course.goal.added',
        {
            'goal': goal,
        }
    )

    # Add a success message
    message = ''
    if str(goal) == CourseGoalType.UNSURE.value:
        message = Text(_('No problem, you can add a goal at any point on the sidebar.'))
    elif str(goal) == CourseGoalType.CERTIFY.value:
        message = Text(_("That's great! You can upgrade to verified status in the sidebar."))
    elif str(goal) == CourseGoalType.COMPLETE.value:
        message = Text(_("That's great! If you decide to upgrade to go for a certified status,"
                         " you can upgrade to a verified status in the sidebar."))
    elif str(goal) == CourseGoalType.EXPLORE.value:
        message = Text(_('Sounds great - We hope you enjoy the course!'))

    # Ensure response is dismissible
    html = HTML('{message}<span tabindex="0" class="icon fa fa-times dismiss"></span>').format(message=message)

    if request.is_ajax():
        return HttpResponse(
            json.dumps({
                'html': html
            }),
            content_type="application/json",
        )


def add_course_goal(user, course_id, goal):
    """
    Given a user, a course id and a goal, create a CourseGoal object
    and save it.
    """
    course_key = CourseKey.from_string(str(course_id))
    new_goal = CourseGoal(user=user, course_key=course_key, goal=goal)
    new_goal.save()


def get_course_goal(user, course_id):
    """
    Given a user and a course id, return their course goal.
    If a course goal does not exist, returns None.
    """
    course_key = CourseKey.from_string(course_id)
    course_goal = CourseGoal.objects.filter(user=user, course_key=course_key)[0]
    return course_goal


def remove_course_goal(user, course_id):
    """
    Given a user and a particular course id, grab any associated
    course goal and delete it. This function deletes any goal found
    which can occur in the unlikely chance that there is a race
    condition while adding a new goal.
    """
    course_key = CourseKey.from_string(str(course_id))
    for goal in CourseGoal.objects.filter(user=user, course_key=course_key):
        goal.delete()
