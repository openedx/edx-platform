"""
Tests for the score change signals defined in the courseware models module.
"""

import ddt
from django.test import TestCase
from django.conf import settings
from mock import patch, MagicMock
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..new import subsection_grade

from ..signals import (
    submissions_score_set_handler,
    submissions_score_reset_handler,
    recalculate_subsection_grade_handler
)


SUBMISSION_SET_KWARGS = {
    'points_possible': 10,
    'points_earned': 5,
    'anonymous_user_id': 'anonymous_id',
    'course_id': 'CourseID',
    'item_id': 'i4x://org/course/usage/123456'
}


SUBMISSION_RESET_KWARGS = {
    'anonymous_user_id': 'anonymous_id',
    'course_id': 'CourseID',
    'item_id': 'i4x://org/course/usage/123456'
}

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


class SubmissionSignalRelayTest(TestCase):
    """
    Tests to ensure that the courseware module correctly catches score_set and
    score_reset signals from the Submissions API and recasts them as LMS
    signals. This ensures that listeners in the LMS only have to handle one type
    of signal for all scoring events.
    """

    def setUp(self):
        """
        Configure mocks for all the dependencies of the render method
        """
        super(SubmissionSignalRelayTest, self).setUp()
        self.signal_mock = self.setup_patch('lms.djangoapps.grades.signals.SCORE_CHANGED.send', None)
        self.user_mock = MagicMock()
        self.user_mock.id = 42
        self.get_user_mock = self.setup_patch('lms.djangoapps.grades.signals.user_by_anonymous_id', self.user_mock)

    def setup_patch(self, function_name, return_value):
        """
        Patch a function with a given return value, and return the mock
        """
        mock = MagicMock(return_value=return_value)
        new_patch = patch(function_name, new=mock)
        new_patch.start()
        self.addCleanup(new_patch.stop)
        return mock

    def test_score_set_signal_handler(self):
        """
        Ensure that, on receipt of a score_set signal from the Submissions API,
        the courseware model correctly converts it to a score_changed signal
        """
        submissions_score_set_handler(None, **SUBMISSION_SET_KWARGS)
        expected_set_kwargs = {
            'sender': None,
            'points_possible': 10,
            'points_earned': 5,
            'user_id': 42,
            'course_id': 'CourseID',
            'usage_id': 'i4x://org/course/usage/123456'
        }
        self.signal_mock.assert_called_once_with(**expected_set_kwargs)

    def test_score_set_user_conversion(self):
        """
        Ensure that the score_set handler properly calls the
        user_by_anonymous_id method to convert from an anonymized ID to a user
        object
        """
        submissions_score_set_handler(None, **SUBMISSION_SET_KWARGS)
        self.get_user_mock.assert_called_once_with('anonymous_id')

    def test_score_set_missing_kwarg(self):
        """
        Ensure that, on receipt of a score_set signal from the Submissions API
        that does not have the correct kwargs, the courseware model does not
        generate a signal.
        """
        for missing in SUBMISSION_SET_KWARGS:
            kwargs = SUBMISSION_SET_KWARGS.copy()
            del kwargs[missing]

            submissions_score_set_handler(None, **kwargs)
            self.signal_mock.assert_not_called()

    def test_score_set_bad_user(self):
        """
        Ensure that, on receipt of a score_set signal from the Submissions API
        that has an invalid user ID, the courseware model does not generate a
        signal.
        """
        self.get_user_mock = self.setup_patch('lms.djangoapps.grades.signals.user_by_anonymous_id', None)
        submissions_score_set_handler(None, **SUBMISSION_SET_KWARGS)
        self.signal_mock.assert_not_called()

    def test_score_reset_signal_handler(self):
        """
        Ensure that, on receipt of a score_reset signal from the Submissions
        API, the courseware model correctly converts it to a score_changed
        signal
        """
        submissions_score_reset_handler(None, **SUBMISSION_RESET_KWARGS)
        expected_reset_kwargs = {
            'sender': None,
            'points_possible': 0,
            'points_earned': 0,
            'user_id': 42,
            'course_id': 'CourseID',
            'usage_id': 'i4x://org/course/usage/123456'
        }
        self.signal_mock.assert_called_once_with(**expected_reset_kwargs)

    def test_score_reset_user_conversion(self):
        """
        Ensure that the score_reset handler properly calls the
        user_by_anonymous_id method to convert from an anonymized ID to a user
        object
        """
        submissions_score_reset_handler(None, **SUBMISSION_RESET_KWARGS)
        self.get_user_mock.assert_called_once_with('anonymous_id')

    def test_score_reset_missing_kwarg(self):
        """
        Ensure that, on receipt of a score_reset signal from the Submissions API
        that does not have the correct kwargs, the courseware model does not
        generate a signal.
        """
        for missing in SUBMISSION_RESET_KWARGS:
            kwargs = SUBMISSION_RESET_KWARGS.copy()
            del kwargs[missing]

            submissions_score_reset_handler(None, **kwargs)
            self.signal_mock.assert_not_called()

    def test_score_reset_bad_user(self):
        """
        Ensure that, on receipt of a score_reset signal from the Submissions API
        that has an invalid user ID, the courseware model does not generate a
        signal.
        """
        self.get_user_mock = self.setup_patch('lms.djangoapps.grades.signals.user_by_anonymous_id', None)
        submissions_score_reset_handler(None, **SUBMISSION_RESET_KWARGS)
        self.signal_mock.assert_not_called()


@patch.dict('django.conf.settings.FEATURES', {'ENABLE_SUBSECTION_GRADES_SAVED': True})
@ddt.ddt
class ScoreChangedUpdatesSubsectionGradeTest(ModuleStoreTestCase):
    def setUp(self):
        """
        Configure mocks for all the dependencies of the render method
        """
        super(ScoreChangedUpdatesSubsectionGradeTest, self).setUp()

        # mock student
        self.user_mock = MagicMock()
        self.user_mock.id = 42
        self.get_user_mock = self.setup_patch('lms.djangoapps.grades.signals.user_by_anonymous_id', self.user_mock)
        self.course = CourseFactory.create(
            org='edx',
            name='course',
            display_name='Verified Course',
            run='run'
        )
        self.course.save()
        self.store.update_item(self.course, 0)
        self.chapter = ItemFactory.create(parent=self.course, category="chapter", display_name="Chapter")
        self.sequential = ItemFactory.create(parent=self.chapter, category='sequential', display_name="Open Sequential")
        self.problem = ItemFactory.create(parent=self.sequential, category='problem', display_name='problem')

        self.SCORE_CHANGED_KWARGS = {
            'points_possible': 10,
            'points_earned': 5,
            'user_id': 'anonymous_id',
            'course_id': self.course.id,
            'usage_id': self.problem.scope_ids.usage_id
        }

        self.update_mock = self.setup_patch(subsection_grade.__name__ + '.SubsectionGradeFactory.update', None)

    def setup_patch(self, function_name, return_value):
        """
        Patch a function with a given return value, and return the mock
        """
        mock = MagicMock(return_value=return_value)
        new_patch = patch(function_name, new=mock)
        new_patch.start()
        self.addCleanup(new_patch.stop)
        return mock

    def test_subsection_grade_updated_on_signal(self):
        recalculate_subsection_grade_handler(None, **self.SCORE_CHANGED_KWARGS)
        self.assertTrue(self.update_mock.called)

    @ddt.data('points_possible', 'points_earned', 'user_id', 'course_id', 'usage_id')
    def test_missing_kwargs(self, kwarg):
        del self.SCORE_CHANGED_KWARGS[kwarg]
        recalculate_subsection_grade_handler(None, **self.SCORE_CHANGED_KWARGS)
        self.assertFalse(self.update_mock.called)
