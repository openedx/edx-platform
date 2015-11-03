"""
Labster wiki tab.
"""

from django.conf import settings
from django.utils.translation import ugettext_noop

from courseware.tabs import ExternalLinkCourseTab


class LabsterWikiTab(ExternalLinkCourseTab):
    """
    Defines the Wiki view type that is shown as a course tab.
    """

    type = "labster_wiki"
    title = ugettext_noop('Theory')
    priority = 35
    is_dynamic = True
    link_value = settings.LABSTER_WIKI_LINK

    def __init__(self, tab_dict=None, name=None, link=None):
        if "type" not in tab_dict:
            tab_dict["type"] = self.type
        if "link" not in tab_dict:
            tab_dict["link"] = self.link_value
        if name is None:
            name = self.title
        super(LabsterWikiTab, self).__init__(tab_dict, name, link)

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Returns true if the wiki is enabled and the specified user is enrolled or has staff access.
        """
        if not settings.LABSTER_FEATURES.get('ENABLE_WIKI'):
            return False
        if course.allow_public_wiki_access:
            return True
        return super(LabsterWikiTab, cls).is_enabled(course, user=user)
