"""
Grades Service Tests
"""


from datetime import datetime

import ddt
import pytz
import six
from freezegun import freeze_time
from mock import call, patch

from lms.djangoapps.grades.constants import GradeOverrideFeatureEnum
from lms.djangoapps.grades.models import (
    PersistentSubsectionGrade,
    PersistentSubsectionGradeOverride
)
from lms.djangoapps.grades.services import GradesService
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..config.waffle import REJECTED_EXAM_OVERRIDES_GRADE
from ..constants import ScoreDatabaseTableEnum


class MockWaffleFlag(object):
    """
    A Mock WaffleFlag object.
    """
    def __init__(self, state):
        self.state = state

    # pylint: disable=unused-argument
    def is_enabled(self, course_key):
        return self.state


@ddt.ddt
class GradesServiceTests(ModuleStoreTestCase):
    """
    Tests for the Grades service
    """

    def setUp(self):
        super(GradesServiceTests, self).setUp()
        self.service = GradesService()
        self.course = CourseFactory.create(org='edX', number='DemoX', display_name='Demo_Course', run='Spring2019')
        self.subsection = ItemFactory.create(parent=self.course, category="subsection", display_name="Subsection")
        self.subsection_without_grade = ItemFactory.create(
            parent=self.course,
            category="subsection",
            display_name="Subsection without grade"
        )
        self.user = UserFactory()
        self.grade = PersistentSubsectionGrade.update_or_create_grade(
            user_id=self.user.id,
            course_id=self.course.id,
            usage_key=self.subsection.location,
            first_attempted=None,
            visible_blocks=[],
            earned_all=6.0,
            possible_all=6.0,
            earned_graded=5.0,
            possible_graded=5.0
        )
        self.signal_patcher = patch('lms.djangoapps.grades.signals.signals.SUBSECTION_OVERRIDE_CHANGED.send')
        self.mock_signal = self.signal_patcher.start()
        self.id_patcher = patch('lms.djangoapps.grades.api.create_new_event_transaction_id')
        self.mock_create_id = self.id_patcher.start()
        self.mock_create_id.return_value = 1
        self.type_patcher = patch('lms.djangoapps.grades.api.set_event_transaction_type')
        self.mock_set_type = self.type_patcher.start()
        self.flag_patcher = patch('lms.djangoapps.grades.config.waffle.waffle_flags')
        self.mock_waffle_flags = self.flag_patcher.start()
        self.mock_waffle_flags.return_value = {
            REJECTED_EXAM_OVERRIDES_GRADE: MockWaffleFlag(True)
        }

    def tearDown(self):
        super(GradesServiceTests, self).tearDown()
        PersistentSubsectionGradeOverride.objects.all().delete()  # clear out all previous overrides
        self.signal_patcher.stop()
        self.id_patcher.stop()
        self.type_patcher.stop()
        self.flag_patcher.stop()

    def subsection_grade_to_dict(self, grade):
        return {
            'earned_all': grade.earned_all,
            'earned_graded': grade.earned_graded
        }

    def subsection_grade_override_to_dict(self, grade):
        return {
            'earned_all_override': grade.earned_all_override,
            'earned_graded_override': grade.earned_graded_override
        }

    def test_get_subsection_grade(self):
        self.assertDictEqual(self.subsection_grade_to_dict(self.service.get_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=self.course.id,
            usage_key_or_id=self.subsection.location
        )), {
            'earned_all': 6.0,
            'earned_graded': 5.0
        })

        # test with id strings as parameters instead
        self.assertDictEqual(self.subsection_grade_to_dict(self.service.get_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=six.text_type(self.course.id),
            usage_key_or_id=six.text_type(self.subsection.location)
        )), {
            'earned_all': 6.0,
            'earned_graded': 5.0
        })

    def test_get_subsection_grade_override(self):
        override, _ = PersistentSubsectionGradeOverride.objects.update_or_create(grade=self.grade)

        self.assertDictEqual(self.subsection_grade_override_to_dict(self.service.get_subsection_grade_override(
            user_id=self.user.id,
            course_key_or_id=self.course.id,
            usage_key_or_id=self.subsection.location
        )), {
            'earned_all_override': override.earned_all_override,
            'earned_graded_override': override.earned_graded_override
        })

        override, _ = PersistentSubsectionGradeOverride.objects.update_or_create(
            grade=self.grade,
            defaults={
                'earned_all_override': 9.0
            }
        )

        # test with course key parameter as string instead
        self.assertDictEqual(self.subsection_grade_override_to_dict(self.service.get_subsection_grade_override(
            user_id=self.user.id,
            course_key_or_id=six.text_type(self.course.id),
            usage_key_or_id=self.subsection.location
        )), {
            'earned_all_override': override.earned_all_override,
            'earned_graded_override': override.earned_graded_override
        })

    @ddt.data(
        {
            'earned_all': 0.0,
            'earned_graded': 0.0
        },
        {
            'earned_all': 0.0,
            'earned_graded': None
        },
        {
            'earned_all': None,
            'earned_graded': None
        },
        {
            'earned_all': 3.0,
            'earned_graded': 2.0
        },
    )
    def test_override_subsection_grade(self, override):
        self.service.override_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=self.course.id,
            usage_key_or_id=self.subsection.location,
            earned_all=override['earned_all'],
            earned_graded=override['earned_graded']
        )

        override_obj = self.service.get_subsection_grade_override(
            self.user.id,
            self.course.id,
            self.subsection.location
        )
        self.assertIsNotNone(override_obj)
        self.assertEqual(override_obj.earned_all_override, override['earned_all'])
        self.assertEqual(override_obj.earned_graded_override, override['earned_graded'])

        self.assertEqual(
            self.mock_signal.call_args,
            call(
                sender=None,
                user_id=self.user.id,
                course_id=six.text_type(self.course.id),
                usage_id=six.text_type(self.subsection.location),
                only_if_higher=False,
                modified=override_obj.modified,
                score_deleted=False,
                score_db_table=ScoreDatabaseTableEnum.overrides
            )
        )

    def test_override_subsection_grade_no_psg(self):
        """
        When there is no PersistentSubsectionGrade associated with the learner
        and subsection to override, one should be created.
        """
        earned_all_override = 2
        earned_graded_override = 0
        self.service.override_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=self.course.id,
            usage_key_or_id=self.subsection_without_grade.location,
            earned_all=earned_all_override,
            earned_graded=earned_graded_override
        )

        # Assert that a new PersistentSubsectionGrade was created
        subsection_grade = self.service.get_subsection_grade(
            self.user.id,
            self.course.id,
            self.subsection_without_grade.location
        )
        self.assertIsNotNone(subsection_grade)
        self.assertEqual(0, subsection_grade.earned_all)
        self.assertEqual(0, subsection_grade.earned_graded)

        # Now assert things about the grade override
        override_obj = self.service.get_subsection_grade_override(
            self.user.id,
            self.course.id,
            self.subsection_without_grade.location
        )
        self.assertIsNotNone(override_obj)
        self.assertEqual(override_obj.earned_all_override, earned_all_override)
        self.assertEqual(override_obj.earned_graded_override, earned_graded_override)

        self.assertEqual(
            self.mock_signal.call_args,
            call(
                sender=None,
                user_id=self.user.id,
                course_id=six.text_type(self.course.id),
                usage_id=six.text_type(self.subsection_without_grade.location),
                only_if_higher=False,
                modified=override_obj.modified,
                score_deleted=False,
                score_db_table=ScoreDatabaseTableEnum.overrides
            )
        )

    @freeze_time('2017-01-01')
    def test_undo_override_subsection_grade(self):
        override, _ = PersistentSubsectionGradeOverride.objects.update_or_create(
            grade=self.grade,
            system=GradeOverrideFeatureEnum.proctoring
        )
        override_id = override.id
        self.service.undo_override_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=self.course.id,
            usage_key_or_id=self.subsection.location,
        )

        override = self.service.get_subsection_grade_override(self.user.id, self.course.id, self.subsection.location)
        self.assertIsNone(override)

        self.assertEqual(
            self.mock_signal.call_args,
            call(
                sender=None,
                user_id=self.user.id,
                course_id=six.text_type(self.course.id),
                usage_id=six.text_type(self.subsection.location),
                only_if_higher=False,
                modified=datetime.now().replace(tzinfo=pytz.UTC),
                score_deleted=True,
                score_db_table=ScoreDatabaseTableEnum.overrides
            )
        )

    def test_undo_override_subsection_grade_across_features(self):
        """
        Test that deletion of subsection grade overrides requested by
        one feature doesn't delete overrides created by another
        feature.
        """
        override, _ = PersistentSubsectionGradeOverride.objects.update_or_create(
            grade=self.grade,
            system=GradeOverrideFeatureEnum.gradebook
        )
        self.service.undo_override_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=self.course.id,
            usage_key_or_id=self.subsection.location,
            feature=GradeOverrideFeatureEnum.proctoring,
        )

        override = self.service.get_subsection_grade_override(self.user.id, self.course.id, self.subsection.location)
        self.assertIsNotNone(override)

    @freeze_time('2018-01-01')
    def test_undo_override_subsection_grade_without_grade(self):
        """
        Test exception handling of `undo_override_subsection_grade` when PersistentSubsectionGrade
        does not exist.
        """

        self.grade.delete()
        try:
            self.service.undo_override_subsection_grade(
                user_id=self.user.id,
                course_key_or_id=self.course.id,
                usage_key_or_id=self.subsection.location,
            )
        except PersistentSubsectionGrade.DoesNotExist:
            assert False, 'Exception raised unexpectedly'

        self.assertFalse(self.mock_signal.called)

    def test_should_override_grade_on_rejected_exam(self):
        self.assertTrue(self.service.should_override_grade_on_rejected_exam('course-v1:edX+DemoX+Demo_Course'))
        self.mock_waffle_flags.return_value = {
            REJECTED_EXAM_OVERRIDES_GRADE: MockWaffleFlag(False)
        }
        self.assertFalse(self.service.should_override_grade_on_rejected_exam('course-v1:edX+DemoX+Demo_Course'))
