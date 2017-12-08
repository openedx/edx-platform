"""
Test signal handlers.
"""

from datetime import datetime

import ddt
import six
from django.test import TestCase
from mock import patch
from opaque_keys.edx.keys import CourseKey
from pytz import utc
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock

from lms.djangoapps.grades.signals.signals import PROBLEM_WEIGHTED_SCORE_CHANGED
from student.tests.factories import UserFactory

from .. import handlers
from ..models import BlockCompletion
from ..test_utils import CompletionWaffleTestMixin


class CustomScorableBlock(XBlock):
    """
    A scorable block with a custom completion strategy.
    """
    has_score = True
    has_custom_completion = True
    completion_mode = XBlockCompletionMode.COMPLETABLE


class ExcludedScorableBlock(XBlock):
    """
    A scorable block that is excluded from completion tracking.
    """
    has_score = True
    has_custom_completion = False
    completion_mode = XBlockCompletionMode.EXCLUDED


@ddt.ddt
class ScorableCompletionHandlerTestCase(CompletionWaffleTestMixin, TestCase):
    """
    Test the signal handler
    """

    def setUp(self):
        super(ScorableCompletionHandlerTestCase, self).setUp()
        self.course_key = CourseKey.from_string('edx/course/beta')
        self.scorable_block_key = self.course_key.make_usage_key(block_type='problem', block_id='red')
        self.user = UserFactory.create()
        self.override_waffle_switch(True)

    def call_scorable_block_completion_handler(self, block_key, score_deleted=None):
        """
        Call the scorable completion signal handler for the specified block.

        Optionally takes a value to pass as score_deleted.
        """
        if score_deleted is None:
            params = {}
        else:
            params = {'score_deleted': score_deleted}
        handlers.scorable_block_completion(
            sender=self,
            user_id=self.user.id,
            course_id=six.text_type(self.course_key),
            usage_id=six.text_type(block_key),
            weighted_earned=0.0,
            weighted_possible=3.0,
            modified=datetime.utcnow().replace(tzinfo=utc),
            score_db_table='submissions',
            **params
        )

    @ddt.data(
        (True, 0.0),
        (False, 1.0),
        (None, 1.0),
    )
    @ddt.unpack
    def test_handler_submits_completion(self, score_deleted, expected_completion):
        self.call_scorable_block_completion_handler(self.scorable_block_key, score_deleted)
        completion = BlockCompletion.objects.get(
            user=self.user,
            course_key=self.course_key,
            block_key=self.scorable_block_key,
        )
        self.assertEqual(completion.completion, expected_completion)

    @XBlock.register_temp_plugin(CustomScorableBlock, 'custom_scorable')
    def test_handler_skips_custom_block(self):
        custom_block_key = self.course_key.make_usage_key(block_type='custom_scorable', block_id='green')
        self.call_scorable_block_completion_handler(custom_block_key)
        completion = BlockCompletion.objects.filter(
            user=self.user,
            course_key=self.course_key,
            block_key=custom_block_key,
        )
        self.assertFalse(completion.exists())

    @XBlock.register_temp_plugin(ExcludedScorableBlock, 'excluded_scorable')
    def test_handler_skips_excluded_block(self):
        excluded_block_key = self.course_key.make_usage_key(block_type='excluded_scorable', block_id='blue')
        self.call_scorable_block_completion_handler(excluded_block_key)
        completion = BlockCompletion.objects.filter(
            user=self.user,
            course_key=self.course_key,
            block_key=excluded_block_key,
        )
        self.assertFalse(completion.exists())

    def test_signal_calls_handler(self):
        user = UserFactory.create()

        with patch('lms.djangoapps.completion.handlers.scorable_block_completion') as mock_handler:
            PROBLEM_WEIGHTED_SCORE_CHANGED.send_robust(
                sender=self,
                user_id=user.id,
                course_id=six.text_type(self.course_key),
                usage_id=six.text_type(self.scorable_block_key),
                weighted_earned=0.0,
                weighted_possible=3.0,
                modified=datetime.utcnow().replace(tzinfo=utc),
                score_db_table='submissions',
            )
        mock_handler.assert_called()


class DisabledCompletionHandlerTestCase(CompletionWaffleTestMixin, TestCase):
    """
    Test that disabling the ENABLE_COMPLETION_TRACKING waffle switch prevents
    the signal handler from submitting a completion.
    """
    def setUp(self):
        super(DisabledCompletionHandlerTestCase, self).setUp()
        self.user = UserFactory.create()
        self.course_key = CourseKey.from_string("course-v1:a+valid+course")
        self.block_key = self.course_key.make_usage_key(block_type="video", block_id="mah-video")
        self.override_waffle_switch(False)

    def test_disabled_handler_does_not_submit_completion(self):
        handlers.scorable_block_completion(
            sender=self,
            user_id=self.user.id,
            course_id=six.text_type(self.course_key),
            usage_id=six.text_type(self.block_key),
            weighted_earned=0.0,
            weighted_possible=3.0,
            modified=datetime.utcnow().replace(tzinfo=utc),
            score_db_table='submissions',
        )
        with self.assertRaises(BlockCompletion.DoesNotExist):
            BlockCompletion.objects.get(
                user=self.user,
                course_key=self.course_key,
                block_key=self.block_key
            )
