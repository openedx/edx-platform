"""
Test signal handlers.
"""

from datetime import datetime

import ddt
from django.test import TestCase
from mock import patch
from opaque_keys.edx.keys import CourseKey
from pytz import utc
import six

from lms.djangoapps.grades.signals.signals import PROBLEM_WEIGHTED_SCORE_CHANGED
from student.tests.factories import UserFactory

from .. import handlers
from ..models import BlockCompletion
from ..test_utils import CompletionWaffleTestMixin


@ddt.ddt
class ScorableCompletionHandlerTestCase(CompletionWaffleTestMixin, TestCase):
    """
    Test the signal handler
    """

    def setUp(self):
        super(ScorableCompletionHandlerTestCase, self).setUp()
        self.user = UserFactory.create()
        self.course_key = CourseKey.from_string("course-v1:a+valid+course")
        self.block_key = self.course_key.make_usage_key(block_type="video", block_id="mah-video")
        self.override_waffle_switch(True)

    @ddt.data(
        ({'score_deleted': True}, 0.0),
        ({'score_deleted': False}, 1.0),
        ({}, 1.0),
    )
    @ddt.unpack
    def test_handler_submits_completion(self, params, expected_completion):
        handlers.scorable_block_completion(
            sender=self,
            user_id=self.user.id,
            course_id=six.text_type(self.course_key),
            usage_id=six.text_type(self.block_key),
            weighted_earned=0.0,
            weighted_possible=3.0,
            modified=datetime.utcnow().replace(tzinfo=utc),
            score_db_table='submissions',
            **params
        )
        completion = BlockCompletion.objects.get(user=self.user, course_key=self.course_key, block_key=self.block_key)
        self.assertEqual(completion.completion, expected_completion)

    def test_signal_calls_handler(self):
        user = UserFactory.create()
        course_key = CourseKey.from_string("course-v1:a+valid+course")
        block_key = course_key.make_usage_key(block_type="video", block_id="mah-video")

        with patch('lms.djangoapps.completion.handlers.scorable_block_completion') as mock_handler:
            PROBLEM_WEIGHTED_SCORE_CHANGED.send_robust(
                sender=self,
                user_id=user.id,
                course_id=six.text_type(course_key),
                usage_id=six.text_type(block_key),
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
