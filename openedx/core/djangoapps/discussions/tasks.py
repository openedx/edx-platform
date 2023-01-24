"""
Tasks for discussions
"""
import logging

from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey
from openedx_events.learning.data import CourseDiscussionConfigurationData, DiscussionTopicContext
from openedx_events.learning.signals import COURSE_DISCUSSIONS_CHANGED
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from .config.waffle import ENABLE_NEW_STRUCTURE_DISCUSSIONS

from .models import DiscussionsConfiguration, Provider
from .utils import get_accessible_discussion_xblocks_by_course_id

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
    COURSE_DISCUSSIONS_CHANGED.send_event(configuration=config_data)


def update_discussions_settings_from_course(course_key: CourseKey) -> CourseDiscussionConfigurationData:
    """
    When there are changes to a course, construct a new data structure containing all the context needed to update the
    course's discussion settings in the database.

    Args:
        course_key (CourseKey): The course that was recently updated.

    Returns:
        (CourseDiscussionConfigurationData): structured discussion configuration data.
    """
    log.info(f"Updating discussion settings for course: {course_key}")
    store = modulestore()

    discussions_config = DiscussionsConfiguration.get(course_key)
    supports_in_context = discussions_config.supports_in_context_discussions()
    provider_type = discussions_config.provider_type

    def iter_discussable_units():
        # Start at 99 so that the initial increment starts it at 100.
        # This leaves the first 100 slots for the course wide topics, which is only a concern if there are more
        # than that many.
        idx = 99
        for section in course.get_children():
            if section.location.block_type != "chapter":
                continue
            for subsection in section.get_children():
                if subsection.location.block_type != "sequential":
                    continue
                for unit in subsection.get_children():
                    if unit.location.block_type != 'vertical':
                        continue
                    # Increment index even for skipped units so that the index is more stable and won't change
                    # if settings change, only if a unit is added or removed.
                    idx += 1
                    # If unit-level visibility is enabled and the unit doesn't have discussion enabled, skip it.
                    if unit_level_visibility and not getattr(unit, "discussion_enabled", False):
                        continue
                    # If the unit is in a graded section and graded sections aren't enabled skip it.
                    if subsection.graded and not enable_graded_units:
                        continue
                    # If the unit is an exam, skip it.
                    if subsection.is_practice_exam or subsection.is_proctored_enabled or subsection.is_time_limited:
                        continue
                    yield DiscussionTopicContext(
                        usage_key=unit.location,
                        title=unit.display_name,
                        group_id=None,
                        ordering=idx,
                        context={
                            "section": section.display_name,
                            "subsection": subsection.display_name,
                            "unit": unit.display_name,
                        },
                    )

    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key)
        enable_in_context = discussions_config.enable_in_context
        provider_config = discussions_config.plugin_configuration
        unit_level_visibility = discussions_config.unit_level_visibility
        enable_graded_units = discussions_config.enable_graded_units
        contexts = []
        if supports_in_context:
            sorted_topics = sorted(
                course.discussion_topics.items(),
                key=lambda item: item[1].get("sort_key", item[0]),
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
            provider_type=provider_type,
            plugin_configuration=provider_config,
            contexts=contexts,
        )
    return config_data


def update_unit_discussion_state_from_discussion_blocks(course_key: CourseKey, user_id: int, force=False) -> None:
    """
    Migrate existing courses to the new mechanism for linking discussion to units.

    This will iterate over an existing course's discussion xblocks and mark the units
    they are in as discussable.

    Args:
        course_key (CourseKey): CourseKey for course.
        user_id (int): User id for the user performing this operation.
        force (bool): Force migration of data even if not using legacy provider

    """
    store = modulestore()
    course = store.get_course(course_key)
    provider = course.discussions_settings.get('provider', None)
    # Only migrate to the new discussion provider if the current provider is the legacy provider.
    if provider is not None and provider != Provider.LEGACY and not force:
        return

    log.info(f"Migrating legacy discussion config for {course_key}")

    with store.bulk_operations(course_key):
        discussion_blocks = get_accessible_discussion_xblocks_by_course_id(course_key, include_all=True)
        discussible_units = {
            discussion_block.parent
            for discussion_block in discussion_blocks
            if discussion_block.parent.block_type == 'vertical'
        }
        log.info(f"Found {len(discussible_units)} discussible unit(s) in {course_key}")
        verticals = store.get_items(course_key, qualifiers={'block_type': 'vertical'})
        graded_subsections = {
            block.location
            for block in store.get_items(
                course_key,
                qualifies={'block_type': 'sequential'},
                settings={'graded': True}
            )
        }
        subsections_with_discussions = set()
        for vertical in verticals:
            if vertical.location in discussible_units:
                vertical.discussion_enabled = True
                subsections_with_discussions.add(vertical.parent)
            else:
                vertical.discussion_enabled = False
            store.update_item(vertical, user_id)

    # If there are any graded subsections that have discussion units,
    # then enable discussions for graded subsections for the course
    enable_graded_subsections = bool(graded_subsections & subsections_with_discussions)

    # If the new discussions experience is enabled globally,
    # then also set up the new provider for the course.
    if ENABLE_NEW_STRUCTURE_DISCUSSIONS.is_enabled():
        log.info(f"New structure is enabled, also updating {course_key} to use new provider")
        course = store.get_course(course_key)
        provider = Provider.OPEN_EDX
        course.discussions_settings['provider'] = provider
        course.discussions_settings['enable_graded_units'] = enable_graded_subsections
        course.discussions_settings['unit_level_visibility'] = True
        store.update_item(course, user_id)
        discussion_config = DiscussionsConfiguration.get(course_key)
        discussion_config.provider_type = provider
        discussion_config.enable_graded_units = enable_graded_subsections
        discussion_config.unit_level_visibility = True
        discussion_config.save()
