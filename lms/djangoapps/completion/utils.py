from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.course_blocks.utils import get_student_module_as_dict
from openedx.core.djangoapps.request_cache.middleware import request_cached
from xmodule.modulestore.django import modulestore
from django.http import HttpRequest


def roll_up(user, course_key):
    print("BF course_key roll_up", course_key)
    course_usage_key = modulestore().make_course_usage_key(course_key)
    print("BF course_usage_key roll_up", course_usage_key)

    # all_blocks = get_blocks(
    #     request,
    #     course_usage_key,
    #     user=request.user,
    #     nav_depth=3,
    #     requested_fields=['children', 'display_name', 'type', 'due', 'graded', 'special_exam_info', 'show_gated_sections', 'format'],
    #     block_types_filter=['course', 'chapter', 'sequential']
    # )
    # print("BF all_blocks", all_blocks)
    
    # completion_service.CompletionService(user, course_key)

    # Get all of the xblocks that are "completable" for the given course
    #course_blocks = get_course_blocks(self._user, self._course_key)

    # Pass the list to the completion_service.get_comletions
    #results = completion_service.get_completions(course_blocks)

    # determine percentage complete

    # fire event to websocket
