"""
Course Goals Python API
"""


from opaque_keys.edx.keys import CourseKey
from rest_framework.reverse import reverse

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.course_goals.models import CourseGoal, GOAL_KEY_CHOICES
from openedx.features.course_experience import ENABLE_COURSE_GOALS


def add_course_goal_deprecated(user, course_id, goal_key):
    """
    Add a new course goal for the provided user and course. If the goal
    already exists, simply update and save the goal.
    This method is for the deprecated version of course goals and will be removed as soon
    as the newer number of days version of course goals is fully implemented.

    Arguments:
        user: The user that is setting the goal
        course_id (string): The id for the course the goal refers to
        goal_key (string): The goal key for the new goal.
    """
    course_key = CourseKey.from_string(str(course_id))
    CourseGoal.objects.update_or_create(
        user=user, course_key=course_key, defaults={'goal_key': goal_key}
    )


def add_course_goal(user, course_id, subscribed_to_reminders, days_per_week=None):
    """
    Add a new course goal for the provided user and course. If the goal
    already exists, simply update and save the goal.

    Arguments:
        user: The user that is setting the goal
        course_id (string): The id for the course the goal refers to
        subscribed_to_reminders (bool): whether the learner wants to receive email reminders about their goal
        days_per_week (int): (optional) number of days learner wants to learn per week
    """
    course_key = CourseKey.from_string(str(course_id))
    defaults = {
        'subscribed_to_reminders': subscribed_to_reminders,
    }
    if days_per_week:
        defaults['days_per_week'] = days_per_week
    CourseGoal.objects.update_or_create(
        user=user, course_key=course_key, defaults=defaults
    )


def get_course_goal(user, course_key):
    """
    Given a user and a course_key, return their course goal.

    If the user is anonymous or a course goal does not exist, returns None.
    """
    if user.is_anonymous:
        return None

    return CourseGoal.objects.filter(user=user, course_key=course_key).first()


def get_goal_api_url(request):
    """
    Returns the endpoint for accessing REST API.
    """
    return reverse('course_goals_api:v0:course_goal-list', request=request)


def has_course_goal_permission(request, course_id, user_access):
    """
    Returns whether the user can access the course goal functionality.

    Only authenticated users that are enrolled in a verifiable course
    can use this feature.
    """
    course_key = CourseKey.from_string(course_id)
    has_verified_mode = CourseMode.has_verified_mode(CourseMode.modes_for_course_dict(course_key))
    return user_access['is_enrolled'] and has_verified_mode and ENABLE_COURSE_GOALS.is_enabled(course_key)


def get_course_goal_options():
    """
    Returns the valid options for goal keys, mapped to their translated
    strings, as defined by theCourseGoal model.
    """
    return dict(GOAL_KEY_CHOICES)


def get_course_goal_text(goal_key):
    """
    Returns the translated string for the given goal key
    """
    goal_options = get_course_goal_options()
    return goal_options[goal_key]


def valid_course_goals_ordered(include_unsure=False):
    """
    Returns a list of the valid options for goal keys ordered by the level of commitment.
    Each option is represented as a tuple, with (goal_key, goal_string).

    This list does not return the unsure option by default since it does not have a relevant commitment level.
    """
    goal_options = get_course_goal_options()

    ordered_goal_options = []
    ordered_goal_options.append((GOAL_KEY_CHOICES.certify, goal_options[GOAL_KEY_CHOICES.certify]))
    ordered_goal_options.append((GOAL_KEY_CHOICES.complete, goal_options[GOAL_KEY_CHOICES.complete]))
    ordered_goal_options.append((GOAL_KEY_CHOICES.explore, goal_options[GOAL_KEY_CHOICES.explore]))

    if include_unsure:
        ordered_goal_options.append((GOAL_KEY_CHOICES.unsure, goal_options[GOAL_KEY_CHOICES.unsure]))

    return ordered_goal_options
