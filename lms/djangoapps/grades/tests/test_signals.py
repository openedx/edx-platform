"""
Tests for the score change signals defined in the courseware models module.
"""

import re

from datetime import datetime
import ddt
from django.test import TestCase
from mock import patch, MagicMock
import pytz
from util.date_utils import to_timestamp

from ..constants import ScoreDatabaseTableEnum
from ..signals.handlers import (
    enqueue_subsection_update,
    submissions_score_set_handler,
    submissions_score_reset_handler,
    problem_raw_score_changed_handler,
)

UUID_REGEX = re.compile(ur'%(hex)s{8}-%(hex)s{4}-%(hex)s{4}-%(hex)s{4}-%(hex)s{12}' % {'hex': u'[0-9a-f]'})

FROZEN_NOW_DATETIME = datetime.now().replace(tzinfo=pytz.UTC)
FROZEN_NOW_TIMESTAMP = to_timestamp(FROZEN_NOW_DATETIME)

SUBMISSION_SET_KWARGS = {
    'points_possible': 10,
    'points_earned': 5,
    'anonymous_user_id': 'anonymous_id',
    'course_id': 'CourseID',
    'item_id': 'i4x://org/course/usage/123456',
    'created_at': FROZEN_NOW_TIMESTAMP,
}

SUBMISSION_RESET_KWARGS = {
    'anonymous_user_id': 'anonymous_id',
    'course_id': 'CourseID',
    'item_id': 'i4x://org/course/usage/123456',
    'created_at': FROZEN_NOW_TIMESTAMP,
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
        [submissions_score_set_handler, SUBMISSION_SET_KWARGS, 5, 10],
        [submissions_score_reset_handler, SUBMISSION_RESET_KWARGS, 0, 0],
    )
    @ddt.unpack
    def test_score_set_signal_handler(self, handler, kwargs, earned, possible):
        """
        Ensure that on receipt of a score_(re)set signal from the Submissions API,
        the signal handler correctly converts it to a PROBLEM_WEIGHTED_SCORE_CHANGED
        signal.

        Also ensures that the handler calls user_by_anonymous_id correctly.
        """
        handler(None, **kwargs)
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
        self.signal_mock.assert_called_once_with(**expected_set_kwargs)
        self.get_user_mock.assert_called_once_with(kwargs['anonymous_user_id'])

    @ddt.data(
        [submissions_score_set_handler, SUBMISSION_SET_KWARGS],
        [submissions_score_reset_handler, SUBMISSION_RESET_KWARGS]
    )
    @ddt.unpack
    def test_score_set_missing_kwarg(self, handler, kwargs):
        """
        Ensure that, on receipt of a score_(re)set signal from the Submissions API
        that does not have the correct kwargs, the courseware model does not
        generate a signal.
        """
        for missing in kwargs:
            local_kwargs = kwargs.copy()
            del local_kwargs[missing]

            with self.assertRaises(KeyError):
                handler(None, **local_kwargs)
            self.signal_mock.assert_not_called()

    @ddt.data(
        [submissions_score_set_handler, SUBMISSION_SET_KWARGS],
        [submissions_score_reset_handler, SUBMISSION_RESET_KWARGS]
    )
    @ddt.unpack
    def test_score_set_bad_user(self, handler, kwargs):
        """
        Ensure that, on receipt of a score_(re)set signal from the Submissions API
        that has an invalid user ID, the courseware model does not generate a
        signal.
        """
        self.get_user_mock = self.setup_patch('lms.djangoapps.grades.signals.handlers.user_by_anonymous_id', None)
        handler(None, **kwargs)
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

    @patch('lms.djangoapps.grades.signals.handlers.log.info')
    def test_subsection_update_logging(self, mocklog):
        enqueue_subsection_update(
            sender='test',
            user_id=1,
            course_id=u'course-v1:edX+Demo_Course+DemoX',
            usage_id=u'block-v1:block-key',
            modified=FROZEN_NOW_DATETIME,
            score_db_table=ScoreDatabaseTableEnum.courseware_student_module,
        )
        log_statement = mocklog.call_args[0][0]
        log_statement = UUID_REGEX.sub(u'*UUID*', log_statement)
        self.assertEqual(
            log_statement,
            (
                u'Grades: Request async calculation of subsection grades with args: '
                u'course_id:course-v1:edX+Demo_Course+DemoX, modified:{time}, '
                u'score_db_table:csm, '
                u'usage_id:block-v1:block-key, user_id:1. Task [*UUID*]'
            ).format(time=FROZEN_NOW_DATETIME)
        )
