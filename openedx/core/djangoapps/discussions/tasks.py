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

    supports_in_context = DiscussionsConfiguration.get(course_key).supports_in_context_discussions()

    def iter_discussable_units():
        sections = store.get_items(course_key, qualifiers={'category': 'sequential'})
        for section in sections:
            for unit in section.get_children():
                # If unit-level visibility is enabled and the unit doesn't have discussion enabled, skip it.
                if unit_level_visibility and not getattr(unit, 'discussion_enabled', False):
                    continue
                # If the unit is in a graded section and graded sections aren't enabled skip it.
                if section.graded and not enable_graded_units:
                    continue
                yield DiscussionTopicContext(
                    usage_key=unit.location,
                    title=unit.display_name,
                    group_id=None,
                )

    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key)
        provider = course.discussions_settings.get('provider')
        enable_in_context = course.discussions_settings.get('enable_in_context', True)
        provider_config = course.discussions_settings.get(provider, {})
        unit_level_visibility = course.discussions_settings.get('unit_level_visibility', False)
        enable_graded_units = course.discussions_settings.get('enable_graded_units', False)
        contexts = []
        if supports_in_context:
            contexts = [
                DiscussionTopicContext(
                    title=topic_name,
                    external_id=topic_config.get('id', None),
                )
                for topic_name, topic_config in course.discussion_topics.items()
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
