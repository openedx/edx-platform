"""
Tests for the score change signals defined in the courseware models module.
"""

import ddt
from django.conf import settings
from django.test import TestCase
from mock import patch, MagicMock
from unittest import skip

from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag
from student.models import anonymous_id_for_user
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

from ..signals.handlers import (
    submissions_score_set_handler,
    submissions_score_reset_handler,
    recalculate_subsection_grade_handler,
)
from ..signals.signals import SCORE_CHANGED


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
        self.signal_mock = self.setup_patch('lms.djangoapps.grades.signals.signals.SCORE_CHANGED.send', None)
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
            'user': self.user_mock,
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

            with self.assertRaises(KeyError):
                submissions_score_set_handler(None, **kwargs)
            self.signal_mock.assert_not_called()

    def test_score_set_bad_user(self):
        """
        Ensure that, on receipt of a score_set signal from the Submissions API
        that has an invalid user ID, the courseware model does not generate a
        signal.
        """
        self.get_user_mock = self.setup_patch('lms.djangoapps.grades.signals.handlers.user_by_anonymous_id', None)
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
            'user': self.user_mock,
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

            with self.assertRaises(KeyError):
                submissions_score_reset_handler(None, **kwargs)
            self.signal_mock.assert_not_called()

    def test_score_reset_bad_user(self):
        """
        Ensure that, on receipt of a score_reset signal from the Submissions API
        that has an invalid user ID, the courseware model does not generate a
        signal.
        """
        self.get_user_mock = self.setup_patch('lms.djangoapps.grades.signals.handlers.user_by_anonymous_id', None)
        submissions_score_reset_handler(None, **SUBMISSION_RESET_KWARGS)
        self.signal_mock.assert_not_called()


@patch.dict(settings.FEATURES, {'PERSISTENT_GRADES_ENABLED_FOR_ALL_TESTS': False})
@ddt.ddt
class ScoreChangedUpdatesSubsectionGradeTest(ModuleStoreTestCase):
    """
    Ensures that upon SCORE_CHANGED signals, the handler
    initiates an update to the affected subsection grade.
    """
    def setUp(self):
        super(ScoreChangedUpdatesSubsectionGradeTest, self).setUp()
        self.user = UserFactory()
        PersistentGradesEnabledFlag.objects.create(enabled_for_all_courses=True, enabled=True)

    def set_up_course(self, enable_subsection_grades=True):
        """
        Configures the course for this test.
        """
        # pylint: disable=attribute-defined-outside-init,no-member
        self.course = CourseFactory.create(
            org='edx',
            name='course',
            run='run',
        )
        if not enable_subsection_grades:
            PersistentGradesEnabledFlag.objects.create(enabled=False)

        self.chapter = ItemFactory.create(parent=self.course, category="chapter", display_name="Chapter")
        self.sequential = ItemFactory.create(parent=self.chapter, category='sequential', display_name="Open Sequential")
        self.problem = ItemFactory.create(parent=self.sequential, category='problem', display_name='problem')

        self.score_changed_kwargs = {
            'points_possible': 10,
            'points_earned': 5,
            'user': self.user,
            'course_id': unicode(self.course.id),
            'usage_id': unicode(self.problem.location),
        }

        # this call caches the anonymous id on the user object, saving 4 queries in all happy path tests
        _ = anonymous_id_for_user(self.user, self.course.id)
        # pylint: enable=attribute-defined-outside-init,no-member

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_subsection_grade_updated_on_signal(self, default_store):
        with self.store.default_store(default_store):
            self.set_up_course()
            self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
            with check_mongo_calls(2) and self.assertNumQueries(11):
                recalculate_subsection_grade_handler(None, **self.score_changed_kwargs)

    def test_single_call_to_create_block_structure(self):
        self.set_up_course()
        self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
        with patch(
            'openedx.core.lib.block_structure.factory.BlockStructureFactory.create_from_cache',
            return_value=None,
        ) as mock_block_structure_create:
            recalculate_subsection_grade_handler(None, **self.score_changed_kwargs)
            self.assertEquals(mock_block_structure_create.call_count, 1)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_query_count_does_not_change_with_more_problems(self, default_store):
        with self.store.default_store(default_store):
            self.set_up_course()
            self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
            ItemFactory.create(parent=self.sequential, category='problem', display_name='problem2')
            ItemFactory.create(parent=self.sequential, category='problem', display_name='problem3')
            with check_mongo_calls(2) and self.assertNumQueries(11):
                recalculate_subsection_grade_handler(None, **self.score_changed_kwargs)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_subsection_grades_not_enabled_on_course(self, default_store):
        with self.store.default_store(default_store):
            self.set_up_course(enable_subsection_grades=False)
            self.assertFalse(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
            with check_mongo_calls(2) and self.assertNumQueries(0):
                recalculate_subsection_grade_handler(None, **self.score_changed_kwargs)

    @skip("Pending completion of TNL-5089")
    @ddt.data(
        (ModuleStoreEnum.Type.mongo, True),
        (ModuleStoreEnum.Type.split, True),
        (ModuleStoreEnum.Type.mongo, False),
        (ModuleStoreEnum.Type.split, False),
    )
    @ddt.unpack
    def test_score_changed_sent_with_feature_flag(self, default_store, feature_flag):
        PersistentGradesEnabledFlag.objects.create(enabled=feature_flag)
        with self.store.default_store(default_store):
            self.set_up_course()
            with check_mongo_calls(0) and self.assertNumQueries(15 if feature_flag else 1):
                SCORE_CHANGED.send(sender=None, **self.score_changed_kwargs)

    @ddt.data('user', 'course_id', 'usage_id')
    def test_missing_kwargs(self, kwarg):
        self.set_up_course()
        self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
        del self.score_changed_kwargs[kwarg]
        with self.assertRaises(KeyError):
            recalculate_subsection_grade_handler(None, **self.score_changed_kwargs)
