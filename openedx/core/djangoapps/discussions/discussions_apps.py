from typing import List, Optional, Type

from django.contrib.auth.models import User
from django.http import HttpRequest
from opaque_keys.edx.keys import LearningContextKey

from edx_django_utils.plugins import PluginManager

DISCUSSION_APPS_NAMESPACE = 'openedx.discussion_apps'


class DiscussionAppCapabilities:
    """ Enum that lists capabilities supported by a discussion tool. """
    LTI1p1 = "lti1.1"
    LTI1p3 = "lti1.3"
    IN_CONTEXT_DISCUSSIONS = "in_context_discussions"
    NOTIFICATIONS = "notifications"
    COHORTS = "cohort_aware"


class DiscussionApp:
    """
    Optional base class for discussion apps.
    """

    # Name of the discussion app for internal use
    name = None
    # Name of the discussion app that will show up in UI
    friendly_name = None
    # A list of capabilities of this discussion app that can't be
    # automatically derived
    capabilities = []
    # The view to render in the course tab page.
    # If the discussion app would like to provide its own view to
    # embed in the main Discussions tab, it can provide it here.
    course_tab_view = None
    # If the discussions apps has mounted its own urls for the tab
    # this can provide the name of that view to reverse to.
    course_tab_view_name = None

    @classmethod
    def is_enabled(
        cls,
        request: Optional[HttpRequest] = None,
        context_key: Optional[LearningContextKey] = None,
        user: Optional[User] = None
    ) -> bool:
        """
        Given a context key, this returns if the plugin is enabled for the course.
        """
        return True


class DiscussionAppsPluginManager(PluginManager):
    """
    Manager for all of the discussion apps that have been made available.

    A discussion app implementation can subclass :class:`DiscussionApp`
    or can implement the required class methods themselves.
    """
    NAMESPACE = DISCUSSION_APPS_NAMESPACE

    @classmethod
    def get_discussion_apps(cls) -> List[Type[DiscussionApp]]:
        """
        Returns the list of available discussion apps.
        """
        return list(cls.get_available_plugins(cls.NAMESPACE).values())
