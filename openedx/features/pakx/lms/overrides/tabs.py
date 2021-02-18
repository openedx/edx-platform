from django.utils.translation import ugettext_noop as _

from courseware.tabs import CourseTab


class OverviewTab(CourseTab):
    """
    A new course tab for course overview
    """
    type = "overview"
    name = "overview"
    title = _("Overview")
    view_name = 'overview_tab_view'
    tab_id = "overview"
    is_default = True
    priority = 20
    online_help_token = 'overview'

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if this tab is enabled."""
        return True
