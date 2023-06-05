"""
All Course Outline related business logic. Do not import from this module
directly. Use openedx.core.djangoapps.content.learning_sequences.api -- that
__init__.py imports from here, and is a more stable place to import from.
"""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

import attr
from django.contrib.auth import get_user_model
from django.db import transaction
from edx_django_utils.cache import TieredCache, get_cache_key
from edx_django_utils.monitoring import function_trace
from opaque_keys.edx.keys import CourseKey, UsageKey

from ..data import (
    CourseOutlineData, CourseSectionData, CourseLearningSequenceData,
    UserCourseOutlineData, UserCourseOutlineDetailsData, VisibilityData,
    CourseVisibility
)
from ..models import (
    CourseSection, CourseSectionSequence, CourseContext, LearningContext, LearningSequence
)
from .permissions import can_see_all_content
from .processors.schedule import ScheduleOutlineProcessor
from .processors.visibility import VisibilityOutlineProcessor
from .processors.enrollment import EnrollmentOutlineProcessor

User = get_user_model()
log = logging.getLogger(__name__)

# Public API...
__all__ = [
    'get_course_outline',
    'get_user_course_outline',
    'get_user_course_outline_details',
    'replace_course_outline',
]


def get_course_outline(course_key: CourseKey) -> CourseOutlineData:
    """
    Get the outline of a course run.

    There is no user-specific data or permissions applied in this function.

    See the definition of CourseOutlineData for details about the data returned.
    """
    course_context = _get_course_context_for_outline(course_key)

    # Check to see if it's in the cache.
    cache_key = "learning_sequences.api.get_course_outline.v1.{}.{}".format(
        course_context.learning_context.context_key, course_context.learning_context.published_version
    )
    outline_cache_result = TieredCache.get_cached_response(cache_key)
    if outline_cache_result.is_found:
        return outline_cache_result.value

    # Fetch model data, and remember that empty Sections should still be
    # represented (so query CourseSection explicitly instead of relying only on
    # select_related from CourseSectionSequence).
    section_models = CourseSection.objects \
        .filter(course_context=course_context) \
        .order_by('ordering')
    section_sequence_models = CourseSectionSequence.objects \
        .filter(course_context=course_context) \
        .order_by('ordering') \
        .select_related('sequence')

    # Build mapping of section.id keys to sequence lists.
    sec_ids_to_sequence_list = defaultdict(list)

    for sec_seq_model in section_sequence_models:
        sequence_model = sec_seq_model.sequence
        sequence_data = CourseLearningSequenceData(
            usage_key=sequence_model.usage_key,
            title=sequence_model.title,
            inaccessible_after_due=sec_seq_model.inaccessible_after_due,
            visibility=VisibilityData(
                hide_from_toc=sec_seq_model.hide_from_toc,
                visible_to_staff_only=sec_seq_model.visible_to_staff_only,
            )
        )
        sec_ids_to_sequence_list[sec_seq_model.section_id].append(sequence_data)

    sections_data = [
        CourseSectionData(
            usage_key=section_model.usage_key,
            title=section_model.title,
            sequences=sec_ids_to_sequence_list[section_model.id],
            visibility=VisibilityData(
                hide_from_toc=section_model.hide_from_toc,
                visible_to_staff_only=section_model.visible_to_staff_only,
            )
        )
        for section_model in section_models
    ]

    outline_data = CourseOutlineData(
        course_key=course_context.learning_context.context_key,
        title=course_context.learning_context.title,
        published_at=course_context.learning_context.published_at,
        published_version=course_context.learning_context.published_version,
        days_early_for_beta=course_context.days_early_for_beta,
        sections=sections_data,
        self_paced=course_context.self_paced,
        course_visibility=CourseVisibility(course_context.course_visibility),
    )
    TieredCache.set_all_tiers(cache_key, outline_data, 300)

    return outline_data


def _get_course_context_for_outline(course_key: CourseKey) -> CourseContext:
    """
    Get Course Context for given param:course_key
    """
    if course_key.deprecated:
        raise ValueError(
            "Learning Sequence API does not support Old Mongo courses: {}"
            .format(course_key),
        )
    try:
        course_context = (
            LearningContext.objects.select_related('course_context').get(context_key=course_key).course_context
        )
    except LearningContext.DoesNotExist:
        # Could happen if it hasn't been published.
        raise CourseOutlineData.DoesNotExist(
            "No CourseOutlineData for {}".format(course_key)
        )
    return course_context


def get_user_course_outline(course_key: CourseKey,
                            user: User,
                            at_time: datetime) -> UserCourseOutlineData:
    """
    Get an outline customized for a particular user at a particular time.

    `user` is a Django User object (including the AnonymousUser)
    `at_time` should be a UTC datetime.datetime object.

    See the definition of UserCourseOutlineData for details about the data
    returned.
    """
    user_course_outline, _ = _get_user_course_outline_and_processors(course_key, user, at_time)
    return user_course_outline


def get_user_course_outline_details(course_key: CourseKey,
                                    user: User,
                                    at_time: datetime) -> UserCourseOutlineDetailsData:
    """
    Get an outline with supplementary data like scheduling information.

    See the definition of UserCourseOutlineDetailsData for details about the
    data returned.
    """
    user_course_outline, processors = _get_user_course_outline_and_processors(
        course_key, user, at_time
    )
    schedule_processor = processors['schedule']

    return UserCourseOutlineDetailsData(
        outline=user_course_outline,
        schedule=schedule_processor.schedule_data(user_course_outline)
    )


def _get_user_course_outline_and_processors(course_key: CourseKey,
                                            user: User,
                                            at_time: datetime):
    full_course_outline = get_course_outline(course_key)
    user_can_see_all_content = can_see_all_content(user, course_key)

    # These are processors that alter which sequences are visible to students.
    # For instance, certain sequences that are intentionally hidden or not yet
    # released. These do not need to be run for staff users. This is where we
    # would add in pluggability for OutlineProcessors down the road.
    processor_classes = [
        ('schedule', ScheduleOutlineProcessor),
        ('visibility', VisibilityOutlineProcessor),
        ('enrollment', EnrollmentOutlineProcessor),
        # Future:
        # ('content_gating', ContentGatingOutlineProcessor),
        # ('milestones', MilestonesOutlineProcessor),
        # ('user_partitions', UserPartitionsOutlineProcessor),
    ]

    # Run each OutlineProcessor in order to figure out what items we have to
    # remove from the CourseOutline.
    processors = dict()
    usage_keys_to_remove = set()
    inaccessible_sequences = set()
    for name, processor_cls in processor_classes:
        # Future optimization: This should be parallelizable (don't rely on a
        # particular ordering).
        processor = processor_cls(course_key, user, at_time)
        processors[name] = processor
        processor.load_data()
        if not user_can_see_all_content:
            # function_trace lets us see how expensive each processor is being.
            with function_trace('processor:{}'.format(name)):
                processor_usage_keys_removed = processor.usage_keys_to_remove(full_course_outline)
                processor_inaccessible_sequences = processor.inaccessible_sequences(full_course_outline)
                usage_keys_to_remove |= processor_usage_keys_removed
                inaccessible_sequences |= processor_inaccessible_sequences

    # Open question: Does it make sense to remove a Section if it has no Sequences in it?
    trimmed_course_outline = full_course_outline.remove(usage_keys_to_remove)
    accessible_sequences = set(trimmed_course_outline.sequences) - inaccessible_sequences

    user_course_outline = UserCourseOutlineData(
        base_outline=full_course_outline,
        user=user,
        at_time=at_time,
        accessible_sequences=accessible_sequences,
        **{
            name: getattr(trimmed_course_outline, name)
            for name in [
                'course_key',
                'title',
                'published_at',
                'published_version',
                'sections',
                'self_paced',
                'course_visibility',
                'days_early_for_beta',
            ]
        }
    )

    return user_course_outline, processors


def replace_course_outline(course_outline: CourseOutlineData):
    """
    Replace the model data stored for the Course Outline with the contents of
    course_outline (a CourseOutlineData).

    This isn't particularly optimized at the moment.
    """
    log.info(
        "Replacing CourseOutline for %s (version %s, %d sequences)",
        course_outline.course_key, course_outline.published_version, len(course_outline.sequences)
    )

    with transaction.atomic():
        # Update or create the basic CourseContext...
        course_context = _update_course_context(course_outline)

        # Wipe out the CourseSectionSequences join+ordering table so we can
        # delete CourseSection and LearningSequence objects more easily.
        course_context.section_sequences.all().delete()

        _update_sections(course_outline, course_context)
        _update_sequences(course_outline, course_context)
        _update_course_section_sequences(course_outline, course_context)


def _update_course_context(course_outline: CourseOutlineData):
    """
    Update CourseContext with given param:course_outline data.
    """
    learning_context, _ = LearningContext.objects.update_or_create(
        context_key=course_outline.course_key,
        defaults={
            'title': course_outline.title,
            'published_at': course_outline.published_at,
            'published_version': course_outline.published_version,
        }
    )
    course_context, created = CourseContext.objects.update_or_create(
        learning_context=learning_context,
        defaults={
            'course_visibility': course_outline.course_visibility.value,
            'days_early_for_beta': course_outline.days_early_for_beta,
            'self_paced': course_outline.self_paced,
        }
    )
    if created:
        log.info("Created new CourseContext for %s", course_outline.course_key)
    else:
        log.info("Found CourseContext for %s, updating...", course_outline.course_key)

    return course_context


def _update_sections(course_outline: CourseOutlineData, course_context: CourseContext):
    """
    Add/Update relevant sections
    """
    for ordering, section_data in enumerate(course_outline.sections):
        CourseSection.objects.update_or_create(
            course_context=course_context,
            usage_key=section_data.usage_key,
            defaults={
                'title': section_data.title,
                'ordering': ordering,
                'hide_from_toc': section_data.visibility.hide_from_toc,
                'visible_to_staff_only': section_data.visibility.visible_to_staff_only,
            }
        )
    # Delete sections that we don't want any more
    section_usage_keys_to_keep = [
        section_data.usage_key for section_data in course_outline.sections
    ]
    CourseSection.objects \
        .filter(course_context=course_context) \
        .exclude(usage_key__in=section_usage_keys_to_keep) \
        .delete()


def _update_sequences(course_outline: CourseOutlineData, course_context: CourseContext):
    """
    Add/Update relevant sequences
    """
    for section_data in course_outline.sections:
        for sequence_data in section_data.sequences:
            LearningSequence.objects.update_or_create(
                learning_context=course_context.learning_context,
                usage_key=sequence_data.usage_key,
                defaults={'title': sequence_data.title}
            )
    LearningSequence.objects \
        .filter(learning_context=course_context.learning_context) \
        .exclude(usage_key__in=course_outline.sequences) \
        .delete()


def _update_course_section_sequences(course_outline: CourseOutlineData, course_context: CourseContext):
    """
    Add/Update relevant course section and sequences
    """
    section_models = {
        section_model.usage_key: section_model
        for section_model
        in CourseSection.objects.filter(course_context=course_context).all()
    }
    sequence_models = {
        sequence_model.usage_key: sequence_model
        for sequence_model
        in LearningSequence.objects.filter(learning_context=course_context.learning_context).all()
    }

    ordering = 0
    for section_data in course_outline.sections:
        for sequence_data in section_data.sequences:
            CourseSectionSequence.objects.update_or_create(
                course_context=course_context,
                section=section_models[section_data.usage_key],
                sequence=sequence_models[sequence_data.usage_key],
                defaults={
                    'ordering': ordering,
                    'inaccessible_after_due': sequence_data.inaccessible_after_due,
                    'hide_from_toc': sequence_data.visibility.hide_from_toc,
                    'visible_to_staff_only': sequence_data.visibility.visible_to_staff_only,
                },
            )
            ordering += 1
