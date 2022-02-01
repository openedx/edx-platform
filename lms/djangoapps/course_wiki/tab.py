"""
These callables are used by django-wiki to check various permissions
a user has on an article.
"""


from django.conf import settings
from django.utils.translation import gettext_noop as _

from lms.djangoapps.courseware.tabs import EnrolledTab


class WikiTab(EnrolledTab):
    """
    Defines the Wiki view type that is shown as a course tab.
    """

    type = "wiki"
    title = _('Wiki')
    view_name = "course_wiki"
    is_hideable = True
    is_default = False
    priority = 70

    def __init__(self, tab_dict):
        # Default to hidden
        super().__init__({"is_hidden": True, **tab_dict})

    def to_json(self):
        json_val = super().to_json()
        # Persist that the tab is *not* hidden
        if not self.is_hidden:
            json_val.update({"is_hidden": False})
        return json_val

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
