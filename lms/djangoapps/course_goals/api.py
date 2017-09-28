"""
Course Goals Python API
"""
from opaque_keys.edx.keys import CourseKey

from .models import CourseGoal


def add_course_goal(user, course_id, goal_key):
    """
    Add a new course goal for the provided user and course.

    Arguments:
        user: The user that is setting the goal
        course_id (string): The id for the course the goal refers to
        goal_key (string): The goal key for the new goal.

    """
    # Create and save a new course goal
    course_key = CourseKey.from_string(str(course_id))
    new_goal = CourseGoal(user=user, course_key=course_key, goal_key=goal_key)
    new_goal.save()


def get_course_goal(user, course_key):
    """
    Given a user and a course_key, return their course goal.

    If a course goal does not exist, returns None.
    """
    course_goals = CourseGoal.objects.filter(user=user, course_key=course_key)
    return course_goals[0] if course_goals else None


def remove_course_goal(user, course_key):
    """
    Given a user and a course_key, remove the course goal.
    """
    course_goal = get_course_goal(user, course_key)
    if course_goal:
        course_goal.delete()
