"""
v0 of the course goals API
"""
from .models import CourseGoal
from opaque_keys.edx.keys import CourseKey

import views


def add_course_goal(user, course_id, goal_key):
    """
    Given a user, a course id and a goal, create a CourseGoal object
    and save it.
    """
    # First ensure that the goal is an acceptable choice
    if goal_key not in views.CourseGoalOption.get_course_goal_keys():
        raise KeyError('Provided goal {goal_key} is not {goal_options}.'.format(
            goal_key=goal_key,
            goal_options=[option.value for option in views.CourseGoalOption],
        ))

    # Remove the existing course goal for the user
    remove_course_goal(user, course_id)

    # Create and save a new course goal
    course_key = CourseKey.from_string(str(course_id))
    new_goal = CourseGoal(user=user, course_key=course_key, goal=goal_key)
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
