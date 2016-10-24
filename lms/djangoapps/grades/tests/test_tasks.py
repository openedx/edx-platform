"""
Tests for the functionality and infrastructure of grades tasks.
"""

from collections import OrderedDict
import ddt
from django.conf import settings
from django.db.utils import IntegrityError
from mock import patch
from unittest import skip

from student.models import anonymous_id_for_user
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag
from lms.djangoapps.grades.signals.signals import SCORE_CHANGED
from lms.djangoapps.grades.tasks import recalculate_subsection_grade


@patch.dict(settings.FEATURES, {'PERSISTENT_GRADES_ENABLED_FOR_ALL_TESTS': False})
@ddt.ddt
class RecalculateSubsectionGradeTest(ModuleStoreTestCase):
    """
    Ensures that the recalculate subsection grade task functions as expected when run.
    """
    def setUp(self):
        super(RecalculateSubsectionGradeTest, self).setUp()
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

        self.score_changed_kwargs = OrderedDict([
            ('user_id', self.user.id),
            ('course_id', unicode(self.course.id)),
            ('usage_id', unicode(self.problem.location)),
            ('only_if_higher', None),
        ])

        # this call caches the anonymous id on the user object, saving 4 queries in all happy path tests
        _ = anonymous_id_for_user(self.user, self.course.id)
        # pylint: enable=attribute-defined-outside-init,no-member

    def test_score_changed_signal_queues_task(self):
        """
        Ensures that the SCORE_CHANGED signal enqueues a recalculate subsection grade task.
        """
        self.set_up_course()
        with patch(
            'lms.djangoapps.grades.tasks.recalculate_subsection_grade.apply_async',
            return_value=None
        ) as mock_task_apply:
            SCORE_CHANGED.send(sender=None, **self.score_changed_kwargs)
            mock_task_apply.assert_called_once_with(args=tuple(self.score_changed_kwargs.values()))

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_subsection_grade_updated(self, default_store):
        with self.store.default_store(default_store):
            self.set_up_course()
            self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
            with check_mongo_calls(2) and self.assertNumQueries(13):
                recalculate_subsection_grade.apply(args=tuple(self.score_changed_kwargs.values()))

    def test_single_call_to_create_block_structure(self):
        self.set_up_course()
        self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
        with patch(
            'openedx.core.lib.block_structure.factory.BlockStructureFactory.create_from_cache',
            return_value=None,
        ) as mock_block_structure_create:
            recalculate_subsection_grade.apply(args=tuple(self.score_changed_kwargs.values()))
            self.assertEquals(mock_block_structure_create.call_count, 1)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_query_count_does_not_change_with_more_problems(self, default_store):
        with self.store.default_store(default_store):
            self.set_up_course()
            self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
            ItemFactory.create(parent=self.sequential, category='problem', display_name='problem2')
            ItemFactory.create(parent=self.sequential, category='problem', display_name='problem3')
            with check_mongo_calls(2) and self.assertNumQueries(13):
                recalculate_subsection_grade.apply(args=tuple(self.score_changed_kwargs.values()))

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_subsection_grades_not_enabled_on_course(self, default_store):
        with self.store.default_store(default_store):
            self.set_up_course(enable_subsection_grades=False)
            self.assertFalse(PersistentGradesEnabledFlag.feature_enabled(self.course.id))
            with check_mongo_calls(2) and self.assertNumQueries(5):
                recalculate_subsection_grade.apply(args=tuple(self.score_changed_kwargs.values()))

    @skip("Pending completion of TNL-5089")
    @ddt.data(
        (ModuleStoreEnum.Type.mongo, True),
        (ModuleStoreEnum.Type.split, True),
        (ModuleStoreEnum.Type.mongo, False),
        (ModuleStoreEnum.Type.split, False),
    )
    @ddt.unpack
    def test_query_counts_with_feature_flag(self, default_store, feature_flag):
        PersistentGradesEnabledFlag.objects.create(enabled=feature_flag)
        with self.store.default_store(default_store):
            self.set_up_course()
            with check_mongo_calls(0) and self.assertNumQueries(3 if feature_flag else 2):
                recalculate_subsection_grade.apply(args=tuple(self.score_changed_kwargs.values()))

    @patch('lms.djangoapps.grades.tasks.recalculate_subsection_grade.retry')
    @patch('lms.djangoapps.grades.new.subsection_grade.SubsectionGradeFactory.update')
    def test_retry_on_integrity_error(self, mock_update, mock_retry):
        """
        Ensures that tasks will be retried if IntegrityErrors are encountered.
        """
        self.set_up_course()
        mock_update.side_effect = IntegrityError("WHAMMY")
        recalculate_subsection_grade.apply(args=tuple(self.score_changed_kwargs.values()))
        self.assertTrue(mock_retry.called)
