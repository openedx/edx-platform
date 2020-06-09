from typing import Iterable, List, Optional

from django.contrib.sites.models import Site
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey

from .data import CourseDiscussionConfigData, DiscussionPluginConfigData
from ..models import DiscussionProviderConfig, LearningContextDiscussionConfig
from ...config_model_utils.models import site_from_org


def _org_and_site_from_course_key(context_key: CourseKey):
    org_key = getattr(context_key, 'org', None)
    site = site_from_org(org_key)
    return org_key, site


def _get_discussion_plugin_config_objects(org_key: str, site: Site) -> Iterable[DiscussionProviderConfig]:
    return DiscussionProviderConfig.objects.filter(
        Q(restrict_to_org__isnull=True, restrict_to_site__isnull=True) |
        Q(restrict_to_org__short_name=org_key) |
        Q(restrict_to_site=site)
    )


def get_course_discussion_config_options(course_key: CourseKey) -> List[DiscussionPluginConfigData]:
    """
    Returns the available discussion configuration options for provided course.

    Args:
        course_key (CourseKey): Learning context, currently only a course

    Returns:
        A list of :class:`DiscussionConfigData` objects.

    """
    org_key, site = _org_and_site_from_course_key(course_key)
    return [
        DiscussionPluginConfigData(
            name=discussion_config.name,
            provider=discussion_config.provider,
            config=discussion_config.config,
        )
        for discussion_config in _get_discussion_plugin_config_objects(org_key, site)
    ]


def get_course_discussion_config(course_key: CourseKey) -> Optional[CourseDiscussionConfigData]:
    """
    Returns the active discussion configuration for the course.

    Args:
        course_key (CourseKey): Learning context, currently only a course

    Returns:
        A :class:`CourseDiscussionConfigData` object with the active configuration for this course.
        Returns `None` if a discussion tool isn't configured for the course yet.

    """
    try:
        course_config = LearningContextDiscussionConfig.objects.get(pk=course_key)
    except LearningContextDiscussionConfig.DoesNotExist:
        return None

    provider_config = course_config.provider_config
    if not provider_config:
        return CourseDiscussionConfigData(
            course_key=course_key,
            config_name=None,
            provider=None,
            config=None,
            enabled=False,
        )
    merged_config = provider_config.config
    merged_config.update(course_config.config_overrides)
    return CourseDiscussionConfigData(
        course_key=course_key,
        config_name=provider_config.name,
        provider=provider_config.provider,
        config=merged_config,
        enabled=course_config.enabled,
    )


def update_course_discussion_config(
    course_key: CourseKey,
    updated_config: dict
) -> Optional[CourseDiscussionConfigData]:
    """
    Updates the configuration for the specified course.

    Args:
        course_key (CourseKey): Learning context, currently only a course
        updated_config (dict): Update configuration to save for specified course

    Returns:
        A :class:`CourseDiscussionConfigData` object with the active configuration for this course.
        Returns `None` if a discussion tool isn't configured for the course yet.

    """
    try:
        course_config = LearningContextDiscussionConfig.objects.get(pk=course_key)
    except LearningContextDiscussionConfig.DoesNotExist:
        raise CourseDiscussionConfigData.DoesNotExist

    provider_config = course_config.provider_config

    if not provider_config:
        raise CourseDiscussionConfigData.DoesNotExist

    course_config.config_overrides = updated_config
    course_config.save()
    return CourseDiscussionConfigData(
        course_key=course_key,
        config_name=provider_config.name,
        provider=provider_config.provider,
        config=updated_config,
        enabled=course_config.enabled,
    )
