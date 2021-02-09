"""
This is where Studio interacts with the learning_sequences application, which
is responsible for holding course outline data. Studio _pushes_ that data into
learning_sequences at publish time.
"""
from datetime import timezone

from edx_django_utils.monitoring import function_trace, set_custom_attribute

from openedx.core.djangoapps.content.learning_sequences.api import replace_course_outline
from openedx.core.djangoapps.content.learning_sequences.data import (
    CourseLearningSequenceData,
    CourseOutlineData,
    CourseSectionData,
    CourseVisibility,
    ExamData,
    VisibilityData,
)
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore


class CourseStructureError(Exception):
    """
    Raise this if we can't create an outline because of the course structure.

    Courses built in Studio conform to a hierarchy that looks like:
        Course -> Section (a.k.a. Chapter) -> Subsection (a.k.a. Sequence)

    OLX imports are much more freeform and can generate unusual structures that
    we won't know how to handle.
    """


def _check_sequence_fields(sequence):
    """
    Raise CourseStructureError if `sequence` is missing a required field.

    Do this instead of checking against specific block types to better future
    proof ourselves against new sequence-types, aliases, changes in the way
    dynamic mixing of XBlock types happens, as well as deprecation/removal of
    the specific fields we care about. If it quacks like a duck...
    """
    expected_fields = [
        'display_name',
        'hide_after_due',
        'hide_from_toc',
        'is_practice_exam',
        'is_proctored_enabled',
        'is_time_limited',
        'visible_to_staff_only',
    ]
    for field in expected_fields:
        if not hasattr(sequence, field):
            msg = (
                f"Cannot create CourseOutline: Expected a Sequence at "
                f"{sequence.location} (child of {sequence.parent}), "
                f"but this object does not have sequence field {field}."
            )
            raise CourseStructureError(msg)


def _check_section_fields(section):
    """
    Raise CourseStructureError if `section` is missing a required field.

    Do this instead of checking against specific block types to better future
    proof ourselves against new sequence-types, aliases, changes in the way
    dynamic mixing of XBlock types happens, as well as deprecation/removal of
    the specific fields we care about. If it quacks like a duck...
    """
    expected_fields = [
        'children',
        'hide_from_toc',
        'visible_to_staff_only',
    ]
    for field in expected_fields:
        if not hasattr(section, field):
            msg = (
                f"Cannot create CourseOutline: Expected a Section at "
                f"{section.location} (child of {section.parent}), "
                f"but this object does not have Section field {field}."
            )
            raise CourseStructureError(msg)


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


def _make_section_data(section):
    """
    Generate a CourseSectionData from a SectionDescriptor.

    This method does a lot of the work to convert modulestore fields to an input
    that the learning_sequences app expects. It doesn't check for specific
    classes (i.e. you could create your own Sequence-like XBlock), but it will
    raise a CourseStructureError if anything you pass in is missing fields that
    we expect in a SectionDescriptor or its SequenceDescriptor children.
    """
    _check_section_fields(section)

    sequences_data = []
    for sequence in section.get_children():
        _check_sequence_fields(sequence)
        sequences_data.append(
            CourseLearningSequenceData(
                usage_key=_remove_version_info(sequence.location),
                title=sequence.display_name,
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
        title=section.display_name,
        sequences=sequences_data,
        visibility=VisibilityData(
            hide_from_toc=section.hide_from_toc,
            visible_to_staff_only=section.visible_to_staff_only,
        ),
    )
    return section_data


@function_trace('get_outline_from_modulestore')
def get_outline_from_modulestore(course_key):
    """
    Get a learning_sequence.data.CourseOutlineData for a param:course_key
    """
    store = modulestore()

    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key, depth=2)
        sections_data = []
        for section in course.get_children():
            section_data = _make_section_data(section)
            sections_data.append(section_data)

        course_outline_data = CourseOutlineData(
            course_key=course_key,
            title=course.display_name,

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
    return course_outline_data


def update_outline_from_modulestore(course_key):
    """
    Update the CourseOutlineData for course_key in the learning_sequences with
    ModuleStore data (i.e. what was most recently published in Studio).
    """
    # Set the course_id attribute first so that if getting the information
    # from the modulestore errors out, we still have the course_key reported in
    # New Relic for easier trace debugging.
    set_custom_attribute('course_id', str(course_key))

    course_outline_data = get_outline_from_modulestore(course_key)
    set_custom_attribute('num_sequences', len(course_outline_data.sequences))
    replace_course_outline(course_outline_data)
