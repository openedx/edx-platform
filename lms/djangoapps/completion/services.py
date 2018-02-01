"""
Runtime service for communicating completion information to the xblock system.
"""
from crum import get_current_request
from lms.djangoapps.course_api.blocks.api import get_blocks
from opaque_keys.edx.keys import CourseKey, UsageKey
from xmodule.modulestore.django import modulestore
from .models import BlockCompletion
from . import waffle


class CompletionService(object):
    """
    Service for handling completions for a user within a course.

    Exposes

    * self.completion_tracking_enabled() -> bool
    * self.get_completions(candidates)

    Constructor takes a user object and course_key as arguments.
    """
    def __init__(self, user, course_key):
        self._user = user
        self._course_key = course_key

    def completion_tracking_enabled(self):
        """
        Exposes ENABLE_COMPLETION_TRACKING waffle switch to XModule runtime

        Return value:

            bool -> True if completion tracking is enabled.
        """
        return waffle.waffle().is_enabled(waffle.ENABLE_COMPLETION_TRACKING)

    def get_completions(self, candidates):
        """
        Given an iterable collection of block_keys in the course, returns a
        mapping of the block_keys to the present completion values of their
        associated blocks.

        If a completion is not found for a given block in the current course,
        0.0 is returned.  The service does not attempt to verify that the block
        exists within the course.

        Parameters:

            candidates: collection of BlockKeys within the current course.

        Return value:

            dict[BlockKey] -> float: Mapping blocks to their completion value.
        """
        completion_queryset = BlockCompletion.objects.filter(
            user=self._user,
            course_key=self._course_key,
            block_key__in=candidates,
        )
        completions = {block.block_key: block.completion for block in completion_queryset}
        for candidate in candidates:
            if candidate not in completions:
                completions[candidate] = 0.0
        return completions

    def get_percent_completed(self, request=None):

        course_usage_key = modulestore().make_course_usage_key(self._course_key)

        if not request:
            request = get_current_request()

        # get all the blocks for the course that are tracked by the completion API
        # NOTE block_types_filter used here is not complete list
        completion_blocks = get_blocks(
            request,
            course_usage_key,
            user=self._user,
            requested_fields=['id'],
            return_type='list',
            block_types_filter=['discussion', 'html', 'problem', 'video', 'poll', 'poll_question', 'openassessment', 'survey']
        )

        print("completion_blocks", completion_blocks)
        block_usage_list = set()
        for block in completion_blocks:
            block_usage_list.add(UsageKey.from_string(block['id']))

        # Ask CompletionService if the course blocks have been completed yet
        completions = self.get_completions(block_usage_list)

        num_completed = sum(completions.values())
        total_blocks = len(completions)
        percent_completed = float(num_completed) / float(total_blocks)

        print("roll_up total_blocks", total_blocks)
        print("roll_up num_completed", num_completed)
        print("roll_up percent_completed", percent_completed)

        return round(percent_completed * 100)
