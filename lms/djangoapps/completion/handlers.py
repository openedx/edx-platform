"""
Signal handlers to trigger completion updates.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth.models import User
from django.dispatch import receiver
from opaque_keys.edx.keys import CourseKey, UsageKey
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock

from lms.djangoapps.grades.signals.signals import PROBLEM_WEIGHTED_SCORE_CHANGED

from . import waffle
from .models import BlockCompletion


@receiver(PROBLEM_WEIGHTED_SCORE_CHANGED)
def scorable_block_completion(sender, **kwargs):  # pylint: disable=unused-argument
    """
    When a problem is scored, submit a new BlockCompletion for that block.
    """
    if not waffle.waffle().is_enabled(waffle.ENABLE_COMPLETION_TRACKING):
        return
    course_key = CourseKey.from_string(kwargs['course_id'])
    block_key = UsageKey.from_string(kwargs['usage_id'])
    block_cls = XBlock.load_class(block_key.block_type)
    if getattr(block_cls, 'completion_mode', XBlockCompletionMode.COMPLETABLE) != XBlockCompletionMode.COMPLETABLE:
        return
    if getattr(block_cls, 'has_custom_completion', False):
        return
    user = User.objects.get(id=kwargs['user_id'])
    if kwargs.get('score_deleted'):
        completion = 0.0
    else:
        completion = 1.0
    BlockCompletion.objects.submit_completion(
        user=user,
        course_key=course_key,
        block_key=block_key,
        completion=completion,
    )
