"""
This is where Studio interacts with the learning_sequences application, which
is responsible for holding course outline data. Studio _pushes_ that data into
learning_sequences at publish time.
"""
from datetime import timezone
from typing import List, Tuple

from edx_django_utils.monitoring import function_trace, set_custom_attribute

from openedx.core.djangoapps.content.learning_sequences.api import replace_course_outline
from openedx.core.djangoapps.content.learning_sequences.data import (
    ContentErrorData,
    CourseLearningSequenceData,
    CourseOutlineData,
    CourseSectionData,
    CourseVisibility,
    ExamData,
    VisibilityData
)
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore


def _remove_version_info(usage_key):
    """
    When we ask modulestore for the published branch in the Studio process
    after catching a publish signal, the items that have been changed will
    return UsageKeys that have full version information in their attached
    CourseKeys. This makes them hash and serialize differently. We want to
    strip this information and have everything use a CourseKey with no
    version information attached.

    The fact that this versioned CourseKey appears is likely an unintended
    side-effect, rather than an intentional part of the API contract. It
    also likely doesn't happen when the modulestore is being processed from
    a different process than the one doing the writing (e.g. a celery task
    running on any environment other than devstack). But stripping this
    version information out is necessary to make devstack and tests work
    properly.
    """
    unversioned_course_key = usage_key.course_key.replace(branch=None, version_guid=None)
    return usage_key.map_into_course(unversioned_course_key)


def _error_for_not_section(not_section):
    """
    ContentErrorData when we run into a child of <course> that's not a Section.

    Has to be phrased in a way that makes sense to course teams.
    """
    return ContentErrorData(
        message=(
            f'<course> contains a <{not_section.location.block_type}> tag with '
            f'url_name="{not_section.location.block_id}" and '
            f'display_name="{getattr(not_section, "display_name", "")}". '
            f'Expected <chapter> tag instead.'
        ),
        usage_key=_remove_version_info(not_section.location),
    )


def _error_for_not_sequence(section, not_sequence):
    """
    ContentErrorData when we run into a child of Section that's not a Sequence.

    Has to be phrased in a way that makes sense to course teams.
    """
    return ContentErrorData(
        message=(
            f'<chapter> with url_name="{section.location.block_id}" and '
            f'display_name="{section.display_name}" contains a '
            f'<{not_sequence.location.block_type}> tag with '
            f'url_name="{not_sequence.location.block_id}" and '
            f'display_name="{getattr(not_sequence, "display_name", "")}". '
            f'Expected a <sequential> tag instead.'
        ),
        usage_key=_remove_version_info(not_sequence.location),
    )


def _make_section_data(section):
    """
    Return a (CourseSectionData, List[ContentDataError]) from a SectionBlock.

    Can return None for CourseSectionData if it's not really a SectionBlock that
    was passed in.

    This method does a lot of the work to convert modulestore fields to an input
    that the learning_sequences app expects. OLX import permits structures that
    are much less constrained than Studio's UI allows for, so whenever we run
    into something that does not meet our Course -> Section -> Subsection
    hierarchy expectations, we add a support-team-readable error message to our
    list of ContentDataErrors to pass back.

    At this point in the code, everything has already been deserialized into
    SectionBlocks and SequenceBlocks, but we're going to phrase our messages in
    ways that would make sense to someone looking at the import OLX, since that
    is the layer that the course teams and support teams are working with.
    """
    section_errors = []

    # First check if it's not a section at all, and short circuit if it isn't.
    if section.location.block_type != 'chapter':
        section_errors.append(_error_for_not_section(section))
        return (None, section_errors)

    # We haven't officially killed off problemset and videosequence yet, so
    # treat them as equivalent to sequential for now.
    valid_sequence_tags = ['sequential', 'problemset', 'videosequence']
    sequences_data = []

    for sequence in section.get_children():
        if sequence.location.block_type not in valid_sequence_tags:
            section_errors.append(_error_for_not_sequence(section, sequence))
            continue

        sequences_data.append(
            CourseLearningSequenceData(
                usage_key=_remove_version_info(sequence.location),
                title=sequence.display_name_with_default,
                inaccessible_after_due=sequence.hide_after_due,
                exam=ExamData(
                    is_practice_exam=sequence.is_practice_exam,
                    is_proctored_enabled=sequence.is_proctored_enabled,
                    is_time_limited=sequence.is_time_limited,
                ),
                visibility=VisibilityData(
                    hide_from_toc=sequence.hide_from_toc,
                    visible_to_staff_only=sequence.visible_to_staff_only,
                ),
            )
        )

    section_data = CourseSectionData(
        usage_key=_remove_version_info(section.location),
        title=section.display_name_with_default,
        sequences=sequences_data,
        visibility=VisibilityData(
            hide_from_toc=section.hide_from_toc,
            visible_to_staff_only=section.visible_to_staff_only,
        ),
    )
    return section_data, section_errors


@function_trace('get_outline_from_modulestore')
def get_outline_from_modulestore(course_key) -> Tuple[CourseOutlineData, List[ContentErrorData]]:
    """
    Return a CourseOutlineData and list of ContentErrorData for param:course_key

    This function does not write any data as a side-effect. It generates a
    CourseOutlineData by inspecting the contents in the modulestore, but does
    not push that data anywhere. This function only operates on the published
    branch, and will not work on Old Mongo courses.
    """
    store = modulestore()
    content_errors = []

    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key, depth=2)
        sections_data = []
        for section in course.get_children():
            section_data, section_errors = _make_section_data(section)
            if section_data:
                sections_data.append(section_data)
            content_errors.extend(section_errors)

        course_outline_data = CourseOutlineData(
            course_key=course_key,
            title=course.display_name_with_default,

            # subtree_edited_on has a tzinfo of bson.tz_util.FixedOffset (which
            # maps to UTC), but for consistency, we're going to use the standard
            # python timezone.utc (which is what the learning_sequence app will
            # return from MySQL). They will compare as equal.
            published_at=course.subtree_edited_on.replace(tzinfo=timezone.utc),

            # .course_version is a BSON obj, so we convert to str (MongoDB-
            # specific objects don't go into CourseOutlineData).
            published_version=str(course.course_version),

            entrance_exam_id=course.entrance_exam_id,
            days_early_for_beta=course.days_early_for_beta,
            sections=sections_data,
            self_paced=course.self_paced,
            course_visibility=CourseVisibility(course.course_visibility),
        )

    return (course_outline_data, content_errors)


def update_outline_from_modulestore(course_key):
    """
    Update the CourseOutlineData for course_key in the learning_sequences with
    ModuleStore data (i.e. what was most recently published in Studio).
    """
    # Set the course_id attribute first so that if getting the information
    # from the modulestore errors out, we still have the course_key reported in
    # New Relic for easier trace debugging.
    set_custom_attribute('course_id', str(course_key))

    course_outline_data, content_errors = get_outline_from_modulestore(course_key)
    set_custom_attribute('num_sequences', len(course_outline_data.sequences))
    set_custom_attribute('num_content_errors', len(content_errors))

    replace_course_outline(course_outline_data, content_errors=content_errors)
