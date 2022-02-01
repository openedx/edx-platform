"""
Tasks for discussions
"""
import logging

from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from .data import CourseDiscussionConfigurationData, DiscussionTopicContext
from .models import DiscussionsConfiguration
from .signals import COURSE_DISCUSSIONS_UPDATED

log = logging.getLogger(__name__)


@shared_task
@set_code_owner_attribute
def update_discussions_settings_from_course_task(course_key_str: str):
    """
    Celery task that creates or updates discussions settings for a course.

    Args:
        course_key_str (str): course key string
    """
    course_key = CourseKey.from_string(course_key_str)
    config_data = update_discussions_settings_from_course(course_key)
    COURSE_DISCUSSIONS_UPDATED.send_event(configuration=config_data)


def update_discussions_settings_from_course(course_key: CourseKey) -> CourseDiscussionConfigurationData:
    """
    When there are changes to a course, construct a new data structure containing all the context needed to update the
    course's discussion settings in the database.

    Args:
        course_key (CourseKey): The course that was recently updated.

    Returns:
        (CourseDiscussionConfigurationData): structured discusion configuration data.
    """
    log.info(f"Updating discussion settings for course: {course_key}")
    store = modulestore()

    discussions_config = DiscussionsConfiguration.get(course_key)
    supports_in_context = discussions_config.supports_in_context_discussions()
    provider_type = discussions_config.provider_type

    def iter_discussable_units():
        sections = store.get_items(course_key, qualifiers={'category': 'sequential'})
        # Start at 99 so that the initial increment starts it at 100.
        # This leaves the first 100 slots for the course wide topics, which is only a concern if there are more
        # than that many.
        idx = 99
        for section in sections:
            for unit in section.get_children():
                # Increment index even for skipped units so that the index is more stable and won't change
                # if settings change, only if a unit is added or removed.
                idx += 1
                # If unit-level visibility is enabled and the unit doesn't have discussion enabled, skip it.
                if unit_level_visibility and not getattr(unit, 'discussion_enabled', False):
                    continue
                # If the unit is in a graded section and graded sections aren't enabled skip it.
                if section.graded and not enable_graded_units:
                    continue
                # If the unit is an exam, skip it.
                if section.is_practice_exam or section.is_proctored_enabled or section.is_time_limited:
                    continue
                yield DiscussionTopicContext(
                    usage_key=unit.location,
                    title=unit.display_name,
                    group_id=None,
                    ordering=idx,
                )

    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key)
        provider = course.discussions_settings.get('provider', provider_type)
        enable_in_context = course.discussions_settings.get('enable_in_context', True)
        provider_config = course.discussions_settings.get(provider, {})
        unit_level_visibility = course.discussions_settings.get('unit_level_visibility', False)
        enable_graded_units = course.discussions_settings.get('enable_graded_units', False)
        contexts = []
        if supports_in_context:
            sorted_topics = sorted(
                course.discussion_topics.items(),
                key=lambda item: item[1].get("sort_key", item[0])
            )
            contexts = [
                DiscussionTopicContext(
                    title=topic_name,
                    external_id=topic_config.get('id', None),
                    ordering=idx,
                )
                for idx, (topic_name, topic_config) in enumerate(sorted_topics)
                if topic_config.get('id', None)
            ]
            if enable_in_context:
                contexts.extend(list(iter_discussable_units()))
        config_data = CourseDiscussionConfigurationData(
            course_key=course_key,
            enable_in_context=enable_in_context,
            enable_graded_units=enable_graded_units,
            unit_level_visibility=unit_level_visibility,
            provider_type=provider,
            plugin_configuration=provider_config,
            contexts=contexts,
        )
    return config_data
