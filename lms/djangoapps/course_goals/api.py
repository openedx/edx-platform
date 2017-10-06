"""
Course Goals Python API
"""
import models

from opaque_keys.edx.keys import CourseKey
from django.conf import settings
from rest_framework.reverse import reverse

from course_modes.models import CourseMode
from openedx.features.course_experience import ENABLE_COURSE_GOALS


def add_course_goal(user, course_id, goal_key):
    """
    Add a new course goal for the provided user and course. If the goal
    already exists, simply update and save the goal.

    Arguments:
        user: The user that is setting the goal
        course_id (string): The id for the course the goal refers to
        goal_key (string): The goal key for the new goal.

    """
    course_key = CourseKey.from_string(str(course_id))
    current_goal = get_course_goal(user, course_key)
    if current_goal:
        # If a course goal already exists, simply update it.
        current_goal.goal_key = goal_key
        current_goal.save(update_fields=['goal_key'])
    else:
        # Otherwise, create and save a new course goal.
        new_goal = models.CourseGoal(user=user, course_key=course_key, goal_key=goal_key)
        new_goal.save()


def get_course_goal(user, course_key):
    """
    Given a user and a course_key, return their course goal.

    If the user is anonymous or a course goal does not exist, returns None.
    """
    if user.is_anonymous():
        return None

    course_goals = models.CourseGoal.objects.filter(user=user, course_key=course_key)
    return course_goals[0] if course_goals else None


def remove_course_goal(user, course_id):
    """
    Given a user and a course_id, remove the course goal.
    """
    course_key = CourseKey.from_string(course_id)
    course_goal = get_course_goal(user, course_key)
    if course_goal:
        course_goal.delete()


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
    has_verified_mode = CourseMode.has_verified_mode(CourseMode.modes_for_course_dict(unicode(course_id)))
    return user_access['is_enrolled'] and has_verified_mode and ENABLE_COURSE_GOALS.is_enabled(course_key) \
        and settings.FEATURES.get('ENABLE_COURSE_GOALS')


def get_course_goal_options():
    """
    Returns the valid options for goal keys, mapped to their translated
    strings, as defined by theCourseGoal model.
    """
    return {goal_key: goal_text for goal_key, goal_text in models.GOAL_KEY_CHOICES}
