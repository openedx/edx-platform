import ddt
import pytz
from datetime import datetime
from freezegun import freeze_time
from lms.djangoapps.grades.models import PersistentSubsectionGrade, PersistentSubsectionGradeOverride
from lms.djangoapps.grades.services import GradesService, _get_key
from mock import patch
from opaque_keys.edx.keys import CourseKey, UsageKey
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..constants import ScoreDatabaseTableEnum


@ddt.ddt
class GradesServiceTests(ModuleStoreTestCase):
    """
    Tests for the Grades service
    """
    def setUp(self, **kwargs):
        super(GradesServiceTests, self).setUp()
        self.service = GradesService()
        self.course = CourseFactory.create(org='edX', number='DemoX', display_name='Demo_Course')
        self.subsection = ItemFactory.create(parent=self.course, category="subsection", display_name="Subsection")
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
        self.patcher = patch('lms.djangoapps.grades.tasks.recalculate_subsection_grade_v3.apply_async')
        self.mock_recalculate = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

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
            course_key_or_id=unicode(self.course.id),
            usage_key_or_id=unicode(self.subsection.location)
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

        # test with id strings as parameters instead
        self.assertDictEqual(self.subsection_grade_override_to_dict(self.service.get_subsection_grade_override(
            user_id=self.user.id,
            course_key_or_id=unicode(self.course.id),
            usage_key_or_id=unicode(self.subsection.location)
        )), {
            'earned_all_override': override.earned_all_override,
            'earned_graded_override': override.earned_graded_override
        })

    @ddt.data(
        [{
            'earned_all': 0.0,
            'earned_graded': 0.0
        }, {
            'earned_all': 0.0,
            'earned_graded': 0.0
        }],
        [{
            'earned_all': 0.0,
            'earned_graded': None
        }, {
            'earned_all': 0.0,
            'earned_graded': 5.0
        }],
        [{
            'earned_all': None,
            'earned_graded': None
        }, {
            'earned_all': 6.0,
            'earned_graded': 5.0
        }],
        [{
            'earned_all': 3.0,
            'earned_graded': 2.0
        }, {
            'earned_all': 3.0,
            'earned_graded': 2.0
        }],
    )
    @ddt.unpack
    def test_override_subsection_grade(self, override, expected):
        PersistentSubsectionGradeOverride.objects.all().delete()  # clear out all previous overrides

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

        self.mock_recalculate.called_with(
            sender=None,
            user_id=self.user.id,
            course_id=unicode(self.course.id),
            usage_id=unicode(self.subsection.location),
            only_if_higher=False,
            expected_modified=override_obj.modified,
            score_db_table=ScoreDatabaseTableEnum.overrides
        )

    @freeze_time('2017-01-01')
    def test_undo_override_subsection_grade(self):
        override, _ = PersistentSubsectionGradeOverride.objects.update_or_create(grade=self.grade)

        self.service.undo_override_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=self.course.id,
            usage_key_or_id=self.subsection.location,
        )

        override = self.service.get_subsection_grade_override(self.user.id, self.course.id, self.subsection.location)
        self.assertIsNone(override)

        self.mock_recalculate.called_with(
            sender=None,
            user_id=self.user.id,
            course_id=unicode(self.course.id),
            usage_id=unicode(self.subsection.location),
            only_if_higher=False,
            expected_modified=datetime.now().replace(tzinfo=pytz.UTC),
            score_deleted=True,
            score_db_table=ScoreDatabaseTableEnum.overrides
        )

    @ddt.data(
        ['edX/DemoX/Demo_Course', CourseKey.from_string('edX/DemoX/Demo_Course'), CourseKey],
        ['course-v1:edX+DemoX+Demo_Course', CourseKey.from_string('course-v1:edX+DemoX+Demo_Course'), CourseKey],
        [CourseKey.from_string('course-v1:edX+DemoX+Demo_Course'),
         CourseKey.from_string('course-v1:edX+DemoX+Demo_Course'), CourseKey],
        ['block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow',
         UsageKey.from_string('block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow'), UsageKey],
        [UsageKey.from_string('block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow'),
         UsageKey.from_string('block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow'), UsageKey],
    )
    @ddt.unpack
    def test_get_key(self, input_key, output_key, key_cls):
        self.assertEqual(_get_key(input_key, key_cls), output_key)
