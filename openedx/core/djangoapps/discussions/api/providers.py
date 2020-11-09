from typing import List, Optional, Type

from opaque_keys.edx.keys import CourseKey, LearningContextKey

from lms.djangoapps.discussion.plugins import CommentServiceDiscussionApp
from .config import get_course_discussion_config
from ..discussions_apps import DiscussionApp, DiscussionAppsPluginManager
from ..models import DiscussionProviderConfig


def get_discussion_provider(context_key: LearningContextKey) -> 'Optional[Type[DiscussionApp]]':
    """
    Returns the discussion app provider associated with the provided context key.

    Args:
        context_key (LearningContextKey): Learning context, currently only a course

    Returns:
        A DiscussionApp instance for the discussion provider associated with this context.
    """
    # Currently, only CourseKeys are supported.
    assert isinstance(context_key, CourseKey)
    config = get_course_discussion_config(context_key)

    # Fall back to the cs comments service Discussion provider
    if config is None:
        return CommentServiceDiscussionApp

    # If the configuration associated with this context is disabled,
    # then we return nothing, and discussion integration will be disabled.
    if config.enabled and config.provider:
        return DiscussionAppsPluginManager.get_plugin(config.provider)


def get_configured_discussion_providers() -> 'List[Type[DiscussionApp]]':
    """
    Returns a list of discussion providers that have a usable configuration.
    """
    configured_providers = DiscussionProviderConfig.objects.values_list('provider', flat=True).distinct()
    return [
        tool
        for tool in DiscussionAppsPluginManager.get_discussion_apps()
        if tool.name in configured_providers
    ]
