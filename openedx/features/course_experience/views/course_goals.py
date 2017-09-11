"""
Helper functions that handle the creating, updating and deleting of course goals.
"""
from django.conf import settings

from student.models import CourseGoal


def set_course_goal(user, course, goal):
    """
    Given a user, a course and a particular goal, save the goal.
    Returns the goal.
    """
    # First assure that the goal is an acceptable choice
    if goal not in settings.COURSE_GOALS['choices'] and goal is not 'dismissible_choice':
        raise KeyError()

    # Remove the existing course goal for the user
    remove_course_goal(user, course)

    # Create and save course goal
    new_goal = CourseGoal(user=user, course_id=course.id, goal=goal)
    new_goal.save()

    return goal


def get_course_goal(user, course):
    """
    Given a user and a course, return their course goal.
    If a course goal does not exist, returns None.
    """
    course_goal = CourseGoal.objects.get(user=user, course_id=course.id)
    return course_goal


def remove_course_goal(user, course):
    old_goal = get_course_goal(user, course)
    if old_goal:
        old_goal.delete()
