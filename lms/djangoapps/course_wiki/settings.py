"""
These callables are used by django-wiki to check various permissions
a user has on an article.
"""

from course_wiki.utils import user_is_article_course_staff


def CAN_DELETE(article, user):  # pylint: disable=invalid-name
    """Is user allowed to soft-delete article?"""
    return _is_staff_for_article(article, user)


def CAN_MODERATE(article, user):  # pylint: disable=invalid-name
    """Is user allowed to restore or purge article?"""
    return _is_staff_for_article(article, user)


def CAN_CHANGE_PERMISSIONS(article, user):  # pylint: disable=invalid-name
    """Is user allowed to change permissions on article?"""
    return _is_staff_for_article(article, user)


def CAN_ASSIGN(article, user):  # pylint: disable=invalid-name
    """Is user allowed to change owner or group of article?"""
    return _is_staff_for_article(article, user)


def CAN_ASSIGN_OWNER(article, user):  # pylint: disable=invalid-name
    """Is user allowed to change group of article to one of its own groups?"""
    return _is_staff_for_article(article, user)


def _is_staff_for_article(article, user):
    """Is the user staff for article's course wiki?"""
    return user.is_staff or user.is_superuser or user_is_article_course_staff(user, article)
