"""
Utils for discussion API.
"""

from lms.djangoapps.discussion.django_comment_client.utils import has_discussion_privileges


def discussion_open_for_user(course, user):
    """
    Check if course discussion are open or not for user.

    Arguments:
            course: Course to check discussions for
            user: User to check for privileges in course
    """
    return course.forum_posts_allowed or has_discussion_privileges(user, course.id)


def set_threads_attribute_value(threads, attribute, value):
    """
    It iterates over thread list and assign thread attribute the value

    Arguments:
        threads: List containing threads
        attribute: the key for thread dict
        value: the value to assign to the thread attribute
    """
    for thread in threads:
        thread[attribute] = value
    return threads
