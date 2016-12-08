"""
Views handling read (GET) requests for the Discussion tab and inline discussions.
"""

from django.conf import settings
from django.utils.translation import ugettext_noop

from courseware.tabs import EnrolledTab
import django_comment_client.utils as utils
from django_component_views.component_views import ComponentView
from xblock.fragment import Fragment
from xmodule.tabs import ComponentTabMixin


class DiscussionTab(ComponentTabMixin, EnrolledTab):
    """
    A tab for the cs_comments_service forums.
    """

    type = 'discussion'
    title = ugettext_noop('Discussion')
    priority = None
    class_name = 'discussion.plugins.DiscussionComponentView'
    is_hideable = settings.FEATURES.get('ALLOW_HIDING_DISCUSSION_TAB', False)
    is_default = False

    @classmethod
    def is_enabled(cls, course, user=None):
        if not super(DiscussionTab, cls).is_enabled(course, user):
            return False
        return utils.is_discussion_enabled(course.id)


class DiscussionComponentView(ComponentView):

    def render_component(request, *args, **kwargs):
        """
        """
        fragment = Fragment()
        fragment.content = "Hello World"
        return fragment
