"""
Course Goals Python API
"""

from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_goals.models import CourseGoal


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
