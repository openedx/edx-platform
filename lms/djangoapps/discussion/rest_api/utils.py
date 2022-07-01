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
