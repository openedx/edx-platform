"""
Tests for the functionality and infrastructure of grades tasks.
"""

from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime, timedelta
import ddt
from django.conf import settings
from django.db.utils import IntegrityError
import itertools
from mock import patch, MagicMock
import pytz
from util.date_utils import to_timestamp

from openedx.core.djangoapps.content.block_structure.exceptions import BlockStructureNotFound
from student.models import anonymous_id_for_user
from student.tests.factories import UserFactory
from track.event_transaction_utils import (
    create_new_event_transaction_id,
    get_event_transaction_id,
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag
from lms.djangoapps.grades.constants import ScoreDatabaseTableEnum
from lms.djangoapps.grades.models import PersistentCourseGrade, PersistentSubsectionGrade
from lms.djangoapps.grades.signals.signals import PROBLEM_WEIGHTED_SCORE_CHANGED
from lms.djangoapps.grades.tasks import recalculate_subsection_grade_v3, RECALCULATE_GRADE_DELAY


@patch.dict(settings.FEATURES, {'PERSISTENT_GRADES_ENABLED_FOR_ALL_TESTS': False})
@ddt.ddt
class RecalculateSubsectionGradeTest(ModuleStoreTestCase):
    """
    Ensures that the recalculate subsection grade task functions as expected when run.
    """
    ENABLED_SIGNALS = ['course_published', 'pre_publish']

    def setUp(self):
        super(RecalculateSubsectionGradeTest, self).setUp()
        self.user = UserFactory()
        PersistentGradesEnabledFlag.objects.create(enabled_for_all_courses=True, enabled=True)

    def set_up_course(self, enable_persistent_grades=True, create_multiple_subsections=False):
        """
        Configures the course for this test.
        """
        # pylint: disable=attribute-defined-outside-init,no-member
        self.course = CourseFactory.create(
            org='edx',
            name='course',
            run='run',
        )
        if not enable_persistent_grades:
            PersistentGradesEnabledFlag.objects.create(enabled=False)

        self.chapter = ItemFactory.create(parent=self.course, category="chapter", display_name="Chapter")
        self.sequential = ItemFactory.create(parent=self.chapter, category='sequential', display_name="Sequential1")
        self.problem = ItemFactory.create(parent=self.sequential, category='problem', display_name='Problem')

        if create_multiple_subsections:
            seq2 = ItemFactory.create(parent=self.chapter, category='sequential')
            ItemFactory.create(parent=seq2, category='problem')

        self.frozen_now_datetime = datetime.now().replace(tzinfo=pytz.UTC)
        self.frozen_now_timestamp = to_timestamp(self.frozen_now_datetime)

        self.problem_weighted_score_changed_kwargs = OrderedDict([
            ('weighted_earned', 1.0),
            ('weighted_possible', 2.0),
            ('user_id', self.user.id),
            ('anonymous_user_id', 5),
            ('course_id', unicode(self.course.id)),
            ('usage_id', unicode(self.problem.location)),
            ('only_if_higher', None),
            ('modified', self.frozen_now_datetime),
            ('score_db_table', ScoreDatabaseTableEnum.courseware_student_module),
        ])

        create_new_event_transaction_id()

        self.recalculate_subsection_grade_kwargs = OrderedDict([
            ('user_id', self.user.id),
            ('course_id', unicode(self.course.id)),
            ('usage_id', unicode(self.problem.location)),
            ('anonymous_user_id', 5),
            ('only_if_higher', None),
            ('expected_modified_time', self.frozen_now_timestamp),
            ('score_deleted', False),
            ('event_transaction_id', unicode(get_event_transaction_id())),
            ('event_transaction_type', u'edx.grades.problem.submitted'),
            ('score_db_table', ScoreDatabaseTableEnum.courseware_student_module),
        ])

        # this call caches the anonymous id on the user object, saving 4 queries in all happy path tests
        _ = anonymous_id_for_user(self.user, self.course.id)
        # pylint: enable=attribute-defined-outside-init,no-member

    @contextmanager
    def mock_get_score(self, score=MagicMock(grade=1.0, max_grade=2.0)):
        """
        Mocks the scores needed by the SCORE_PUBLISHED signal
        handler. By default, sets the returned score to 1/2.
        """
        with patch("lms.djangoapps.grades.tasks.get_score", return_value=score):
            yield

    def test_triggered_by_problem_weighted_score_change(self):
        """
        Ensures that the PROBLEM_WEIGHTED_SCORE_CHANGED signal enqueues the correct task.
        """
        self.set_up_course()
        send_args = self.problem_weighted_score_changed_kwargs
        local_task_args = self.recalculate_subsection_grade_kwargs.copy()
        local_task_args['event_transaction_type'] = u'edx.grades.problem.submitted'
        with self.mock_get_score() and patch(
            'lms.djangoapps.grades.tasks.recalculate_subsection_grade_v3.apply_async',
            return_value=None
        ) as mock_task_apply:
            PROBLEM_WEIGHTED_SCORE_CHANGED.send(sender=None, **send_args)
            mock_task_apply.assert_called_once_with(countdown=RECALCULATE_GRADE_DELAY, kwargs=local_task_args)

    @patch('lms.djangoapps.grades.signals.signals.SUBSECTION_SCORE_CHANGED.send')
    def test_triggers_subsection_score_signal(self, mock_subsection_signal):
        """
        Ensures that a subsection grade recalculation triggers a signal.
        """
        self.set_up_course()
        self._apply_recalculate_subsection_grade()
        self.assertTrue(mock_subsection_signal.called)

    def test_block_structure_created_only_once(self):
        self.set_up_course()
        self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
        with patch(
            'openedx.core.djangoapps.content.block_structure.factory.BlockStructureFactory.create_from_store',
            side_effect=BlockStructureNotFound(self.course.location),
        ) as mock_block_structure_create:
            self._apply_recalculate_subsection_grade()
            self.assertEquals(mock_block_structure_create.call_count, 1)

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 1, 26, True),
        (ModuleStoreEnum.Type.mongo, 1, 23, False),
        (ModuleStoreEnum.Type.split, 3, 25, True),
        (ModuleStoreEnum.Type.split, 3, 22, False),
    )
    @ddt.unpack
    def test_query_counts(self, default_store, num_mongo_calls, num_sql_calls, create_multiple_subsections):
        with self.store.default_store(default_store):
            self.set_up_course(create_multiple_subsections=create_multiple_subsections)
            self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
            with check_mongo_calls(num_mongo_calls):
                with self.assertNumQueries(num_sql_calls):
                    self._apply_recalculate_subsection_grade()

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 1, 26),
        (ModuleStoreEnum.Type.split, 3, 25),
    )
    @ddt.unpack
    def test_query_counts_dont_change_with_more_content(self, default_store, num_mongo_calls, num_sql_calls):
        with self.store.default_store(default_store):
            self.set_up_course(create_multiple_subsections=True)
            self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))

            num_problems = 10
            for _ in range(num_problems):
                ItemFactory.create(parent=self.sequential, category='problem')

            num_sequentials = 10
            for _ in range(num_sequentials):
                ItemFactory.create(parent=self.chapter, category='sequential')

            with check_mongo_calls(num_mongo_calls):
                with self.assertNumQueries(num_sql_calls):
                    self._apply_recalculate_subsection_grade()

    @patch('lms.djangoapps.grades.signals.signals.SUBSECTION_SCORE_CHANGED.send')
    def test_other_inaccessible_subsection(self, mock_subsection_signal):
        self.set_up_course()
        accessible_seq = ItemFactory.create(parent=self.chapter, category='sequential')
        inaccessible_seq = ItemFactory.create(parent=self.chapter, category='sequential', visible_to_staff_only=True)

        # Update problem to have 2 additional sequential parents.
        # So in total, 3 sequential parents, with one inaccessible.
        for sequential in (accessible_seq, inaccessible_seq):
            sequential.children = [self.problem.location]
            modulestore().update_item(sequential, self.user.id)  # pylint: disable=no-member

        # Make sure the signal is sent for only the 2 accessible sequentials.
        self._apply_recalculate_subsection_grade()
        self.assertEquals(mock_subsection_signal.call_count, 2)
        sequentials_signalled = {
            args[1]['subsection_grade'].location
            for args in mock_subsection_signal.call_args_list
        }
        self.assertSetEqual(
            sequentials_signalled,
            {self.sequential.location, accessible_seq.location},
        )

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 1, 11),
        (ModuleStoreEnum.Type.split, 3, 10),
    )
    @ddt.unpack
    def test_persistent_grades_not_enabled_on_course(self, default_store, num_mongo_queries, num_sql_queries):
        with self.store.default_store(default_store):
            self.set_up_course(enable_persistent_grades=False)
            with check_mongo_calls(num_mongo_queries):
                with self.assertNumQueries(num_sql_queries):
                    self._apply_recalculate_subsection_grade()
            with self.assertRaises(PersistentCourseGrade.DoesNotExist):
                PersistentCourseGrade.read_course_grade(self.user.id, self.course.id)
            self.assertEqual(len(PersistentSubsectionGrade.bulk_read_grades(self.user.id, self.course.id)), 0)

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 1, 24),
        (ModuleStoreEnum.Type.split, 3, 23),
    )
    @ddt.unpack
    def test_persistent_grades_enabled_on_course(self, default_store, num_mongo_queries, num_sql_queries):
        with self.store.default_store(default_store):
            self.set_up_course(enable_persistent_grades=True)
            with check_mongo_calls(num_mongo_queries):
                with self.assertNumQueries(num_sql_queries):
                    self._apply_recalculate_subsection_grade()
            self.assertIsNotNone(PersistentCourseGrade.read_course_grade(self.user.id, self.course.id))
            self.assertGreater(len(PersistentSubsectionGrade.bulk_read_grades(self.user.id, self.course.id)), 0)

    @patch('lms.djangoapps.grades.signals.signals.SUBSECTION_SCORE_CHANGED.send')
    @patch('lms.djangoapps.grades.new.subsection_grade.SubsectionGradeFactory.update')
    def test_retry_first_time_only(self, mock_update, mock_course_signal):
        """
        Ensures that a task retry completes after a one-time failure.
        """
        self.set_up_course()
        mock_update.side_effect = [IntegrityError("WHAMMY"), None]
        self._apply_recalculate_subsection_grade()
        self.assertEquals(mock_course_signal.call_count, 1)

    @patch('lms.djangoapps.grades.tasks.recalculate_subsection_grade_v3.retry')
    @patch('lms.djangoapps.grades.new.subsection_grade.SubsectionGradeFactory.update')
    def test_retry_on_integrity_error(self, mock_update, mock_retry):
        """
        Ensures that tasks will be retried if IntegrityErrors are encountered.
        """
        self.set_up_course()
        mock_update.side_effect = IntegrityError("WHAMMY")
        self._apply_recalculate_subsection_grade()
        self._assert_retry_called(mock_retry)

    @ddt.data(ScoreDatabaseTableEnum.courseware_student_module, ScoreDatabaseTableEnum.submissions)
    @patch('lms.djangoapps.grades.tasks.recalculate_subsection_grade_v3.retry')
    @patch('lms.djangoapps.grades.tasks.log')
    def test_retry_when_db_not_updated(self, score_db_table, mock_log, mock_retry):
        self.set_up_course()
        self.recalculate_subsection_grade_kwargs['score_db_table'] = score_db_table
        modified_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(days=1)
        if score_db_table == ScoreDatabaseTableEnum.submissions:
            with patch('lms.djangoapps.grades.tasks.sub_api.get_score') as mock_sub_score:
                mock_sub_score.return_value = {
                    'created_at': modified_datetime
                }
                self._apply_recalculate_subsection_grade(
                    mock_score=MagicMock(module_type='any_block_type')
                )
        else:
            self._apply_recalculate_subsection_grade(
                mock_score=MagicMock(modified=modified_datetime)
            )

        self._assert_retry_called(mock_retry)
        self.assertIn(
            u"Persistent Grades: tasks._has_database_updated_with_new_score is False.",
            mock_log.info.call_args_list[0][0][0]
        )

    @ddt.data(
        *itertools.product(
            (True, False),
            (ScoreDatabaseTableEnum.courseware_student_module, ScoreDatabaseTableEnum.submissions),
        )
    )
    @ddt.unpack
    @patch('lms.djangoapps.grades.tasks.recalculate_subsection_grade_v3.retry')
    @patch('lms.djangoapps.grades.tasks.log')
    def test_when_no_score_found(self, score_deleted, score_db_table, mock_log, mock_retry):
        self.set_up_course()
        self.recalculate_subsection_grade_kwargs['score_deleted'] = score_deleted
        self.recalculate_subsection_grade_kwargs['score_db_table'] = score_db_table

        if score_db_table == ScoreDatabaseTableEnum.submissions:
            with patch('lms.djangoapps.grades.tasks.sub_api.get_score') as mock_sub_score:
                mock_sub_score.return_value = None
                self._apply_recalculate_subsection_grade(
                    mock_score=MagicMock(module_type='any_block_type')
                )
        else:
            self._apply_recalculate_subsection_grade(mock_score=None)

        if score_deleted:
            self._assert_retry_not_called(mock_retry)
        else:
            self._assert_retry_called(mock_retry)
            self.assertIn(
                u"Persistent Grades: tasks._has_database_updated_with_new_score is False.",
                mock_log.info.call_args_list[0][0][0]
            )

    @patch('lms.djangoapps.grades.tasks.log')
    @patch('lms.djangoapps.grades.tasks.recalculate_subsection_grade_v3.retry')
    @patch('lms.djangoapps.grades.new.subsection_grade.SubsectionGradeFactory.update')
    def test_log_unknown_error(self, mock_update, mock_retry, mock_log):
        """
        Ensures that unknown errors are logged before a retry.
        """
        self.set_up_course()
        mock_update.side_effect = Exception("General exception with no further detail!")
        self._apply_recalculate_subsection_grade()
        self.assertIn("General exception with no further detail!", mock_log.info.call_args[0][0])
        self._assert_retry_called(mock_retry)

    @patch('lms.djangoapps.grades.tasks.log')
    @patch('lms.djangoapps.grades.tasks.recalculate_subsection_grade_v3.retry')
    @patch('lms.djangoapps.grades.new.subsection_grade.SubsectionGradeFactory.update')
    def test_no_log_known_error(self, mock_update, mock_retry, mock_log):
        """
        Ensures that known errors are not logged before a retry.
        """
        self.set_up_course()
        mock_update.side_effect = IntegrityError("race condition oh noes")
        self._apply_recalculate_subsection_grade()
        self.assertFalse(mock_log.info.called)
        self._assert_retry_called(mock_retry)

    def _apply_recalculate_subsection_grade(
            self,
            mock_score=MagicMock(modified=datetime.utcnow().replace(tzinfo=pytz.UTC) + timedelta(days=1))
    ):
        """
        Calls the recalculate_subsection_grade task with necessary
        mocking in place.
        """
        with self.mock_get_score(mock_score):
            recalculate_subsection_grade_v3.apply(kwargs=self.recalculate_subsection_grade_kwargs)

    def _assert_retry_called(self, mock_retry):
        """
        Verifies the task was retried and with the correct
        number of arguments.
        """
        self.assertTrue(mock_retry.called)
        self.assertEquals(len(mock_retry.call_args[1]['kwargs']), len(self.recalculate_subsection_grade_kwargs))

    def _assert_retry_not_called(self, mock_retry):
        """
        Verifies the task was not retried.
        """
        self.assertFalse(mock_retry.called)
