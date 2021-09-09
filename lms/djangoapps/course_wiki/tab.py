"""
These callables are used by django-wiki to check various permissions
a user has on an article.
"""


from django.conf import settings
from django.utils.translation import gettext_noop

from lms.djangoapps.courseware.tabs import EnrolledTab


class WikiTab(EnrolledTab):
    """
    Defines the Wiki view type that is shown as a course tab.
    """

    type = "wiki"
    title = gettext_noop('Wiki')
    view_name = "course_wiki"
    is_hideable = True
    is_default = False

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Returns true if the wiki is enabled and the specified user is enrolled or has staff access.
        """
        if not settings.WIKI_ENABLED:
            return False
        if course.allow_public_wiki_access:
            return True
        return super().is_enabled(course, user=user)
