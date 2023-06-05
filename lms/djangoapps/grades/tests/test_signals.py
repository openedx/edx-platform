"""
Tests for the score change signals defined in the courseware models module.
"""


import re
from datetime import datetime

import ddt
import pytz
from django.test import TestCase
from mock import MagicMock, patch
from submissions.models import score_reset, score_set

from common.djangoapps.util.date_utils import to_timestamp

from ..constants import ScoreDatabaseTableEnum
from ..signals.handlers import (
    disconnect_submissions_signal_receiver,
    problem_raw_score_changed_handler,
    submissions_score_reset_handler,
    submissions_score_set_handler
)
from ..signals.signals import PROBLEM_RAW_SCORE_CHANGED

UUID_REGEX = re.compile(u'%(hex)s{8}-%(hex)s{4}-%(hex)s{4}-%(hex)s{4}-%(hex)s{12}' % {'hex': u'[0-9a-f]'})

FROZEN_NOW_DATETIME = datetime.now().replace(tzinfo=pytz.UTC)
FROZEN_NOW_TIMESTAMP = to_timestamp(FROZEN_NOW_DATETIME)

SUBMISSIONS_SCORE_SET_HANDLER = 'submissions_score_set_handler'
SUBMISSIONS_SCORE_RESET_HANDLER = 'submissions_score_reset_handler'
HANDLERS = {
    SUBMISSIONS_SCORE_SET_HANDLER: submissions_score_set_handler,
    SUBMISSIONS_SCORE_RESET_HANDLER: submissions_score_reset_handler,
}

SUBMISSION_SET_KWARGS = 'submission_set_kwargs'
SUBMISSION_RESET_KWARGS = 'submission_reset_kwargs'
SUBMISSION_KWARGS = {
    SUBMISSION_SET_KWARGS: {
        'points_possible': 10,
        'points_earned': 5,
        'anonymous_user_id': 'anonymous_id',
        'course_id': 'CourseID',
        'item_id': 'i4x://org/course/usage/123456',
        'created_at': FROZEN_NOW_TIMESTAMP,
    },
    SUBMISSION_RESET_KWARGS: {
        'anonymous_user_id': 'anonymous_id',
        'course_id': 'CourseID',
        'item_id': 'i4x://org/course/usage/123456',
        'created_at': FROZEN_NOW_TIMESTAMP,
    },
}

PROBLEM_RAW_SCORE_CHANGED_KWARGS = {
    'raw_earned': 1.0,
    'raw_possible': 2.0,
    'weight': 4,
    'user_id': 'UserID',
    'course_id': 'CourseID',
    'usage_id': 'i4x://org/course/usage/123456',
    'only_if_higher': False,
    'score_deleted': True,
    'modified': FROZEN_NOW_TIMESTAMP,
    'score_db_table': ScoreDatabaseTableEnum.courseware_student_module,
    'grader_response': None
}

PROBLEM_WEIGHTED_SCORE_CHANGED_KWARGS = {
    'sender': None,
    'weighted_earned': 2.0,
    'weighted_possible': 4.0,
    'user_id': 'UserID',
    'course_id': 'CourseID',
    'usage_id': 'i4x://org/course/usage/123456',
    'only_if_higher': False,
    'score_deleted': True,
    'modified': FROZEN_NOW_TIMESTAMP,
    'score_db_table': ScoreDatabaseTableEnum.courseware_student_module,
    'grader_response': None
}


@ddt.ddt
class ScoreChangedSignalRelayTest(TestCase):
    """
    Tests to ensure that the courseware module correctly catches
    (a) score_set and score_reset signals from the Submissions API
    (b) LMS PROBLEM_RAW_SCORE_CHANGED signals
    and recasts them as LMS PROBLEM_WEIGHTED_SCORE_CHANGED signals.

    This ensures that listeners in the LMS only have to handle one type
    of signal for all scoring events regardless of their origin.
    """
    SIGNALS = {
        'score_set': score_set,
        'score_reset': score_reset,
    }

    def setUp(self):
        """
        Configure mocks for all the dependencies of the render method
        """
        super(ScoreChangedSignalRelayTest, self).setUp()
        self.signal_mock = self.setup_patch(
            'lms.djangoapps.grades.signals.signals.PROBLEM_WEIGHTED_SCORE_CHANGED.send',
            None,
        )
        self.user_mock = MagicMock()
        self.user_mock.id = 42
        self.get_user_mock = self.setup_patch(
            'lms.djangoapps.grades.signals.handlers.user_by_anonymous_id',
            self.user_mock
        )

    def setup_patch(self, function_name, return_value):
        """
        Patch a function with a given return value, and return the mock
        """
        mock = MagicMock(return_value=return_value)
        new_patch = patch(function_name, new=mock)
        new_patch.start()
        self.addCleanup(new_patch.stop)
        return mock

    @ddt.data(
        [SUBMISSIONS_SCORE_SET_HANDLER, SUBMISSION_SET_KWARGS, 5, 10],
        [SUBMISSIONS_SCORE_RESET_HANDLER, SUBMISSION_RESET_KWARGS, 0, 0],
    )
    @ddt.unpack
    def test_score_set_signal_handler(self, handler_name, kwargs, earned, possible):
        """
        Ensure that on receipt of a score_(re)set signal from the Submissions API,
        the signal handler correctly converts it to a PROBLEM_WEIGHTED_SCORE_CHANGED
        signal.

        Also ensures that the handler calls user_by_anonymous_id correctly.
        """
        local_kwargs = SUBMISSION_KWARGS[kwargs].copy()
        handler = HANDLERS[handler_name]
        handler(None, **local_kwargs)
        expected_set_kwargs = {
            'sender': None,
            'weighted_possible': possible,
            'weighted_earned': earned,
            'user_id': self.user_mock.id,
            'anonymous_user_id': 'anonymous_id',
            'course_id': 'CourseID',
            'usage_id': 'i4x://org/course/usage/123456',
            'modified': FROZEN_NOW_TIMESTAMP,
            'score_db_table': 'submissions',
        }
        if kwargs == SUBMISSION_RESET_KWARGS:
            expected_set_kwargs['score_deleted'] = True
        self.signal_mock.assert_called_once_with(**expected_set_kwargs)
        self.get_user_mock.assert_called_once_with(local_kwargs['anonymous_user_id'])

    def test_tnl_6599_zero_possible_bug(self):
        """
        Ensure that, if coming from the submissions API, signals indicating a
        a possible score of 0 are swallowed for reasons outlined in TNL-6559.
        """
        local_kwargs = SUBMISSION_KWARGS[SUBMISSION_SET_KWARGS].copy()
        local_kwargs['points_earned'] = 0
        local_kwargs['points_possible'] = 0
        submissions_score_set_handler(None, **local_kwargs)
        self.signal_mock.assert_not_called()

    @ddt.data(
        [SUBMISSIONS_SCORE_SET_HANDLER, SUBMISSION_SET_KWARGS],
        [SUBMISSIONS_SCORE_RESET_HANDLER, SUBMISSION_RESET_KWARGS]
    )
    @ddt.unpack
    def test_score_set_missing_kwarg(self, handler_name, kwargs):
        """
        Ensure that, on receipt of a score_(re)set signal from the Submissions API
        that does not have the correct kwargs, the courseware model does not
        generate a signal.
        """
        handler = HANDLERS[handler_name]
        for missing in SUBMISSION_KWARGS[kwargs]:
            local_kwargs = SUBMISSION_KWARGS[kwargs].copy()
            del local_kwargs[missing]

            with self.assertRaises(KeyError):
                handler(None, **local_kwargs)
            self.signal_mock.assert_not_called()

    @ddt.data(
        [SUBMISSIONS_SCORE_SET_HANDLER, SUBMISSION_SET_KWARGS],
        [SUBMISSIONS_SCORE_RESET_HANDLER, SUBMISSION_RESET_KWARGS]
    )
    @ddt.unpack
    def test_score_set_bad_user(self, handler_name, kwargs):
        """
        Ensure that, on receipt of a score_(re)set signal from the Submissions API
        that has an invalid user ID, the courseware model does not generate a
        signal.
        """
        handler = HANDLERS[handler_name]
        self.get_user_mock = self.setup_patch('lms.djangoapps.grades.signals.handlers.user_by_anonymous_id', None)
        handler(None, **SUBMISSION_KWARGS[kwargs])
        self.signal_mock.assert_not_called()

    def test_raw_score_changed_signal_handler(self):
        problem_raw_score_changed_handler(None, **PROBLEM_RAW_SCORE_CHANGED_KWARGS)
        expected_set_kwargs = PROBLEM_WEIGHTED_SCORE_CHANGED_KWARGS.copy()
        self.signal_mock.assert_called_with(**expected_set_kwargs)

    def test_raw_score_changed_score_deleted_optional(self):
        local_kwargs = PROBLEM_RAW_SCORE_CHANGED_KWARGS.copy()
        del local_kwargs['score_deleted']
        problem_raw_score_changed_handler(None, **local_kwargs)
        expected_set_kwargs = PROBLEM_WEIGHTED_SCORE_CHANGED_KWARGS.copy()
        expected_set_kwargs['score_deleted'] = False
        self.signal_mock.assert_called_with(**expected_set_kwargs)

    @ddt.data(
        ['score_set', SUBMISSION_KWARGS[SUBMISSION_SET_KWARGS]['points_earned'],
         SUBMISSION_SET_KWARGS],
        ['score_reset', 0,
         SUBMISSION_RESET_KWARGS]
    )
    @ddt.unpack
    def test_disconnect_manager(self, signal_name, weighted_earned, kwargs):
        """
        Tests to confirm the disconnect_submissions_signal_receiver context manager is working correctly.
        """
        signal = self.SIGNALS[signal_name]
        kwargs = SUBMISSION_KWARGS[kwargs].copy()
        handler_mock = self.setup_patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send',
                                        None)

        # Receiver connected before we start
        signal.send(None, **kwargs)
        handler_mock.assert_called_once()
        # Make sure the correct handler was called
        assert handler_mock.call_args[1]['weighted_earned'] == weighted_earned
        handler_mock.reset_mock()

        # Disconnect is functioning
        with disconnect_submissions_signal_receiver(signal):
            signal.send(None, **kwargs)
            handler_mock.assert_not_called()
            handler_mock.reset_mock()

        # And we reconnect properly afterwards
        signal.send(None, **kwargs)
        handler_mock.assert_called_once()
        assert handler_mock.call_args[1]['weighted_earned'] == weighted_earned

    def test_disconnect_manager_bad_arg(self):
        """
        Tests that the disconnect context manager errors when given an invalid signal.
        """
        with self.assertRaises(ValueError):
            with disconnect_submissions_signal_receiver(PROBLEM_RAW_SCORE_CHANGED):
                pass
