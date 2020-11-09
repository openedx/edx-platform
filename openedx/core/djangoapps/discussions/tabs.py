from typing import Callable, Optional, Type

from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404, HttpRequest
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_noop
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from common.lib.xmodule.xmodule.course_module import CourseDescriptor
from common.lib.xmodule.xmodule.tabs import TabFragmentViewMixin
from lms.djangoapps.courseware.tabs import EnrolledTab
from .api.providers import get_discussion_provider
from .discussions_apps import DiscussionApp


class DiscussionTab(TabFragmentViewMixin, EnrolledTab):
    """
    A tab for the discussion forums.
    """

    type = 'discussion'
    title = ugettext_noop('Discussion')
    priority = None
    is_hideable = settings.FEATURES.get('ALLOW_HIDING_DISCUSSION_TAB', False)
    is_default = False
    body_class = 'discussion'
    online_help_token = 'discussions'

    def __init__(self, tab_dict):
        super().__init__(tab_dict)
        self._discussion_provider = None

    def _get_discussion_provider(self, course_id: CourseKey) -> Type[DiscussionApp]:
        if not self._discussion_provider:
            self._discussion_provider = get_discussion_provider(course_id)
        return self._discussion_provider

    def _get_tab_view(self, course_key):
        provider = self._get_discussion_provider(course_key)
        if not provider:
            raise Http404
        tab_view = provider.course_tab_view
        if isinstance(tab_view, str):
            tab_view = import_string(tab_view)
        return tab_view()

    @property
    def link_func(self) -> Callable[[CourseDescriptor, Callable], str]:
        def inner_link_func(course, reverse_func):
            provider = self._get_discussion_provider(course.id)
            if provider.course_tab_view_name:
                return reverse_func(provider.course_tab_view_name, args=[str(course.id)])
            else:
                return reverse_func("course_tab_view", args=[str(course.id), self.type])

        return inner_link_func

    def render_to_fragment(self, request: HttpRequest, course: CourseDescriptor, **kwargs) -> Fragment:
        """
        Renders this tab to a web fragment.
        """
        tab_view = self._get_tab_view(course.id)
        return tab_view.render_to_fragment(request, course_id=str(course.id), **kwargs)

    @classmethod
    def is_enabled(cls, course: CourseDescriptor, user: Optional[User] = None) -> bool:
        if not super(DiscussionTab, cls).is_enabled(course, user):
            return False
        provider = get_discussion_provider(course.id)
        return provider and provider.course_tab_view and provider.is_enabled(context_key=course.id)

    @property
    def uses_bootstrap(self) -> bool:
        """
        Returns true if this tab is rendered with Bootstrap.
        """
        return True
