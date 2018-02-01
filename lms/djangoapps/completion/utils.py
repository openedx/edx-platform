from crum import get_current_request
from channels import Group
import json
from lms.djangoapps.course_api.blocks.api import get_blocks
from opaque_keys.edx.keys import CourseKey, UsageKey
from xmodule.modulestore.django import modulestore
from .services import CompletionService


def roll_up(user, course_key):

    course_usage_key = modulestore().make_course_usage_key(course_key)
    request = get_current_request()

    # get all the blocks for the course that are tracked by the completion API
    # NOTE block_types_filter used here is not complete list
    completion_blocks = get_blocks(
        request,
        course_usage_key,
        user=request.user,
        requested_fields=['id'],
        return_type='list',
        block_types_filter=['discussion', 'html', 'problem', 'video', 'poll', 'poll_question', 'openassessment', 'survey']
    )

    print("completion_blocks", completion_blocks)
    block_usage_list = set()
    for block in completion_blocks:
        block_usage_list.add(UsageKey.from_string(block['id']))

    # Ask CompletionService if the course blocks have been completed yet
    completion_service = CompletionService(user, course_key)
    completions = completion_service.get_completions(block_usage_list)

    num_completed = sum(completions.values())
    total_blocks = len(completions)
    percent_completed = float(num_completed) / float(total_blocks)

    print("roll_up total_blocks", total_blocks)
    print("roll_up num_completed", num_completed)
    print("roll_up percent_completed", percent_completed)

    # fire event to websocket
    Group('completion').send(
        {'text': json.dumps({
            'course_id': str(course_key),
            'percent_complete': round(percent_completed * 100, 2),
        })}
    )