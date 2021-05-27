"""
Common utilities for the course experience, including course outline.
"""

from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.course_blocks.api import get_course_blocks
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.cache_utils import request_cached
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from common.djangoapps.student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore


@request_cached()
def get_course_outline_block_tree(request, course_id, user=None, allow_start_dates_in_future=False):  # lint-amnesty, pylint: disable=too-many-statements
    """
    Returns the root block of the course outline, with children as blocks.

    allow_start_dates_in_future (bool): When True, will allow blocks to be
            returned that can bypass the StartDateTransformer's filter to show
            blocks with start dates in the future.
    """

    assert user is None or user.is_authenticated

    course_key = CourseKey.from_string(course_id)
    course_usage_key = modulestore().make_course_usage_key(course_key)

    all_blocks = get_blocks(
        request,
        course_usage_key,
        user=user,
        nav_depth=3,
        requested_fields=[
            'children',
            'contains_gated_content',
            'display_name',
            'due',
            'effort_activities',
            'effort_time',
            'format',
            'graded',
            'has_score',
            'show_gated_sections',
            'special_exam_info',
            'start',
            'type',
            'weight',
            'completion',
            'complete',
            'resume_block',
        ],
        allow_start_dates_in_future=allow_start_dates_in_future,
    )

    course_outline_root_block = all_blocks['blocks'].get(all_blocks['root'], None)
    return course_outline_root_block


def get_resume_block(block):
    """
    Gets the deepest block marked as 'resume_block'.

    """
    if block.get('authorization_denial_reason') or not block.get('resume_block'):
        return None
    if not block.get('children'):
        return block

    for child in block['children']:
        resume_block = get_resume_block(child)
        if resume_block:
            return resume_block
    return block


def get_start_block(block):
    """
    Gets the deepest block to use as the starting block.
    """
    if not block.get('children'):
        return block

    first_child = block['children'][0]

    return get_start_block(first_child)


def dates_banner_should_display(course_key, user):
    """
    Return whether or not the reset banner should display,
    determined by whether or not a course has any past-due,
    incomplete sequentials and which enrollment mode is being
    dealt with for the current user and course.

    Returns:
        (missed_deadlines, missed_gated_content):
            missed_deadlines is True if the user has missed any graded content deadlines
            missed_gated_content is True if the first content that the user missed was gated content
    """
    if not RELATIVE_DATES_FLAG.is_enabled(course_key):
        return False, False

    course_overview = CourseOverview.objects.get(id=str(course_key))

    # Only display the banner for self-paced courses
    if not course_overview.self_paced:
        return False, False

    # Only display the banner for enrolled users
    if not CourseEnrollment.is_enrolled(user, course_key):
        return False, False

    # Don't display the banner if the course has ended
    if course_overview.end and course_overview.end < timezone.now():
        return False, False

    store = modulestore()
    course_usage_key = store.make_course_usage_key(course_key)
    block_data = get_course_blocks(user, course_usage_key, include_completion=True)
    for section_key in block_data.get_children(course_usage_key):
        for subsection_key in block_data.get_children(section_key):
            subsection_due_date = block_data.get_xblock_field(subsection_key, 'due', None)
            if (subsection_due_date and subsection_due_date < timezone.now() and
                    not is_block_structure_complete_for_assignments(block_data, subsection_key)):
                # Display the banner if the due date for an incomplete graded subsection has passed
                return True, block_data.get_xblock_field(subsection_key, 'contains_gated_content', False)

    # Don't display the banner if there were no missed deadlines
    return False, False


def is_block_structure_complete_for_assignments(block_data, block_key):
    """
    Considers a block complete only if all scored & graded leaf blocks are complete.

    This is different from the normal `complete` flag because children of the block that are informative (like
    readings or videos) do not count. We only care about actual homework content.
    """
    children = block_data.get_children(block_key)
    if children:
        return all(is_block_structure_complete_for_assignments(block_data, child_key) for child_key in children)

    category = block_data.get_xblock_field(block_key, 'category')
    if category in ('course', 'chapter', 'sequential', 'vertical'):
        # If there are no children for these "hierarchy" block types, just bail. This could be because the
        # content isn't available yet (start date in future) or we're too late and the block has hide_after_due
        # set. Or maybe a different transformer cut off content for whatever reason. Regardless of the cause - if the
        # user can't see this content and we continue, we might accidentally say this block is complete because it
        # isn't scored (which most hierarchy blocks wouldn't be).
        return False

    complete = block_data.get_xblock_field(block_key, 'complete', False)
    graded = block_data.get_xblock_field(block_key, 'graded', False)
    has_score = block_data.get_xblock_field(block_key, 'has_score', False)
    weight = block_data.get_xblock_field(block_key, 'weight', 1)
    scored = has_score and (weight is None or weight > 0)

    return complete or not graded or not scored
