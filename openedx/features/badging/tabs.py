from django.utils.translation import ugettext_noop
from xmodule.tabs import CourseTab


class BadgingTab(CourseTab):
    """ The my badges new tab view. """
    type = 'my_badges'
    title = ugettext_noop('My Badges')
    priority = 20
    view_name = 'my_badges'
    tab_id = 'my_badges'
    is_dynamic = True
    is_default = False

    @classmethod
    def is_enabled(cls, course, user=None):
        return True

