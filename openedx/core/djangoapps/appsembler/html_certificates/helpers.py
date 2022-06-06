"""
Appsembler Helpers to improve course info in learner dashboard.
We should remove this after Maple, since all the info is in the new course_home_api.
"""

import beeline

from xmodule.modulestore.django import modulestore
from common.djangoapps.student.helpers import cert_info
from lms.djangoapps.course_blocks.api import get_course_blocks


@beeline.traced('html_certificates.get_course_blocks_completion_summary')
def get_course_blocks_completion_summary(course_key, user):
    """
    Returns an object with the number of complete units, incomplete units, and units that contain gated content
    for the given course. The complete and incomplete counts only reflect units that are able to be completed by
    the given user. If a unit contains gated content, it is not counted towards the incomplete count.
    The object contains fields: complete_count, incomplete_count, locked_count
    """
    if not user.id:
        return {}

    beeline.add_context_field('username', user.username)
    beeline.add_context_field('course_key', course_key)

    store = modulestore()
    course_usage_key = store.make_course_usage_key(course_key)
    block_data = get_course_blocks(user, course_usage_key, allow_start_dates_in_future=True, include_completion=True)

    complete_count, incomplete_count, locked_count = 0, 0, 0
    for section_key in block_data.get_children(course_usage_key):  # pylint: disable=too-many-nested-blocks
        for subsection_key in block_data.get_children(section_key):
            for unit_key in block_data.get_children(subsection_key):
                complete = block_data.get_xblock_field(unit_key, 'complete', False)
                contains_gated_content = block_data.get_xblock_field(unit_key, 'contains_gated_content', False)
                if contains_gated_content:
                    locked_count += 1
                elif complete:
                    complete_count += 1
                else:
                    incomplete_count += 1

    return {
        'complete_count': complete_count,
        'incomplete_count': incomplete_count,
        'locked_count': locked_count
    }
