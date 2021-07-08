"""
Common utilities for the course experience, including course outline.
"""


from datetime import timedelta

from completion.models import BlockCompletion
from django.db.models import Q
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey
from six.moves import range

from course_modes.models import CourseMode
from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.course_blocks.utils import get_student_module_as_dict
from lms.djangoapps.courseware.access import has_access
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.cache_utils import request_cached
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore


@request_cached()
def get_course_outline_block_tree(request, course_id, user=None, allow_start_dates_in_future=False):
    """
    Returns the root block of the course outline, with children as blocks.

    allow_start_dates_in_future (bool): When True, will allow blocks to be
            returned that can bypass the StartDateTransformer's filter to show
            blocks with start dates in the future.
    """

    assert user is None or user.is_authenticated

    def populate_children(block, all_blocks):
        """
        Replace each child id with the full block for the child.

        Given a block, replaces each id in its children array with the full
        representation of that child, which will be looked up by id in the
        passed all_blocks dict. Recursively do the same replacement for children
        of those children.
        """
        children = block.get('children', [])

        for i in range(len(children)):
            child_id = block['children'][i]
            child_detail = populate_children(all_blocks[child_id], all_blocks)
            block['children'][i] = child_detail

        return block

    def recurse_mark_scored(block):
        """
        Mark this block as 'scored' if any of its descendents are 'scored' (that is, 'has_score' and 'weight' > 0).
        """
        is_scored = block.get('has_score', False) and block.get('weight', 1) > 0
        # Use a list comprehension to force the recursion over all children, rather than just stopping
        # at the first child that is scored.
        children_scored = any([recurse_mark_scored(child) for child in block.get('children', [])])
        if is_scored or children_scored:
            block['scored'] = True
            return True
        else:
            block['scored'] = False
            return False

    def recurse_num_graded_problems(block):
        """
        Marks each block with the number of graded and scored leaf blocks below it as 'num_graded_problems'
        """
        is_scored = block.get('has_score') and block.get('weight', 1) > 0
        is_graded = block.get('graded')
        is_countable = block.get('type') not in ('lti', 'lti_consumer')
        is_graded_problem = is_scored and is_graded and is_countable

        num_graded_problems = 1 if is_graded_problem else 0
        num_graded_problems += sum(recurse_num_graded_problems(child) for child in block.get('children', []))

        block['num_graded_problems'] = num_graded_problems
        return num_graded_problems

    def recurse_mark_auth_denial(block):
        """
        Mark this block as 'scored' if any of its descendents are 'scored' (that is, 'has_score' and 'weight' > 0).
        """
        own_denial_reason = {block['authorization_denial_reason']} if 'authorization_denial_reason' in block else set()
        # Use a list comprehension to force the recursion over all children, rather than just stopping
        # at the first child that is scored.
        child_denial_reasons = own_denial_reason.union(
            *(recurse_mark_auth_denial(child) for child in block.get('children', []))
        )
        if child_denial_reasons:
            block['all_denial_reasons'] = child_denial_reasons
        return child_denial_reasons

    course_key = CourseKey.from_string(course_id)
    course_usage_key = modulestore().make_course_usage_key(course_key)

    all_blocks = get_blocks(
        request,
        course_usage_key,
        user=request.user,
        nav_depth=3,
        requested_fields=[
            'children',
            'display_name',
            'type',
            'start',
            'contains_gated_content',
            'due',
            'graded',
            'has_score',
            'weight',
            'completion',
            'complete',
            'resume_block',
        ],
        allow_start_dates_in_future=allow_start_dates_in_future,
    )

    course_outline_root_block = all_blocks['blocks'].get(all_blocks['root'], None)
    if course_outline_root_block:
        populate_children(course_outline_root_block, all_blocks['blocks'])
        recurse_mark_scored(course_outline_root_block)
        recurse_num_graded_problems(course_outline_root_block)
        recurse_mark_auth_denial(course_outline_root_block)
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


def dates_banner_should_display(course_key, request):
    """
    Return whether or not the reset banner should display,
    determined by whether or not a course has any past-due,
    incomplete sequentials and which enrollment mode is being
    dealt with for the current user and course.
    """
    missed_deadlines = False
    course_enrollment = None
    if RELATIVE_DATES_FLAG.is_enabled(str(course_key)):
        course_overview = CourseOverview.objects.get(id=str(course_key))
        course_end_date = getattr(course_overview, 'end_date', None)
        is_self_paced = getattr(course_overview, 'self_paced', False)
        is_course_staff = bool(
            request.user and course_overview and has_access(request.user, 'staff', course_overview, course_overview.id)
        )
        if is_self_paced and (not is_course_staff) and (not course_end_date or timezone.now() < course_end_date):
            course_enrollment = CourseEnrollment.objects.filter(
                course=course_overview, user=request.user,
            ).filter(
                Q(mode=CourseMode.AUDIT) | Q(mode=CourseMode.VERIFIED)
            ).first()
            if course_enrollment:
                store = modulestore()
                course_usage_key = store.make_course_usage_key(course_key)
                block_data = get_course_blocks(request.user, course_usage_key, include_completion=True)
                for section_key in block_data.get_children(course_usage_key):
                    if missed_deadlines:
                        break
                    for subsection_key in block_data.get_children(section_key):
                        if (
                            not block_data.get_xblock_field(subsection_key, 'complete', False)
                            and block_data.get_xblock_field(subsection_key, 'graded', False)
                            and block_data.get_xblock_field(
                                subsection_key, 'due', timezone.now() + timedelta(1)) < timezone.now()
                        ):
                            missed_deadlines = True
                            break

    return missed_deadlines, getattr(course_enrollment, 'mode', None)
