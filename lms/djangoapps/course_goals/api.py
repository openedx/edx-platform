"""
Course Goals Python API
"""
from enum import Enum
from eventtracking import tracker
from opaque_keys.edx.keys import CourseKey
from django.utils.translation import ugettext as _
from openedx.core.djangolib.markup import Text

from models import CourseGoal
import views


def add_course_goal(user, course_id, goal_key):
    """
    Create a CourseGoal object and save it. If a goal already
    exist for that user in the particular course, update the
    goal to reflect the newly set goal_key.

    Arguments:
        user: The user that is setting the goal
        course_id (string): The id for the course the goal refers to
        goal_key (string): The goal key that maps to one of the
            enumerated goal keys from CourseGoalOption.

    """
    # First ensure that the goal is an acceptable choice
    if goal_key not in views.CourseGoalOption.get_course_goal_keys():
        raise KeyError('Provided goal {goal_key} is not {goal_options}.'.format(
            goal_key=goal_key,
            goal_options=[option.value for option in views.CourseGoalOption],
        ))

    # Create and save a new course goal
    course_key = CourseKey.from_string(str(course_id))
    new_goal = CourseGoal(user=user, course_key=course_key, goal_key=goal_key)
    new_goal.save()

    # Log the event
    tracker.emit(
        'edx.course.goal.added',
        {
            'course_key': course_key,
            'goal_key': goal_key,
        }
    )


def get_course_goal(user, course_id):
    """
    Given a user and a course id (string), return their course goal_key.

    If a course goal does not exist, returns None.
    """
    course_key = CourseKey.from_string(course_id)
    course_goals = CourseGoal.objects.filter(user=user, course_key=course_key)
    return course_goals[0] if course_goals else None


class CourseGoalOption(Enum):
    """
    Types of goals that a user can select.

    These options are set to a string goal key so that they can be
    referenced elsewhere in the code when necessary.
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
    a translated, user-facing string to be used to represent that
    particular goal.
    """
    return {
        CourseGoalOption.CERTIFY.value: Text(_('Earn a certificate')),
        CourseGoalOption.COMPLETE.value: Text(_('Complete the course')),
        CourseGoalOption.EXPLORE.value: Text(_('Explore the course')),
        CourseGoalOption.UNSURE.value: Text(_('Not sure yet')),
    }[goal_option]
