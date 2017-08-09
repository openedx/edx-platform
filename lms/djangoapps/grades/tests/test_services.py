import ddt
import pytz
from datetime import datetime
from freezegun import freeze_time
from lms.djangoapps.grades.models import PersistentSubsectionGrade, PersistentSubsectionGradeOverride
from lms.djangoapps.grades.services import GradesService, _get_key
from lms.djangoapps.grades.signals.handlers import SUBSECTION_OVERRIDE_EVENT_TYPE
from mock import patch, call
from opaque_keys.edx.keys import CourseKey, UsageKey
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..config.waffle import REJECTED_EXAM_OVERRIDES_GRADE
from ..constants import ScoreDatabaseTableEnum


class MockWaffleFlag():
    def __init__(self, state):
        self.state = state

    def is_enabled(self, course_key):
        return self.state


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
        self.signal_patcher = patch('lms.djangoapps.grades.signals.signals.SUBSECTION_OVERRIDE_CHANGED.send')
        self.mock_signal = self.signal_patcher.start()
        self.id_patcher = patch('lms.djangoapps.grades.services.create_new_event_transaction_id')
        self.mock_create_id = self.id_patcher.start()
        self.mock_create_id.return_value = 1
        self.type_patcher = patch('lms.djangoapps.grades.services.set_event_transaction_type')
        self.mock_set_type = self.type_patcher.start()
        self.flag_patcher = patch('lms.djangoapps.grades.services.waffle_flags')
        self.mock_waffle_flags = self.flag_patcher.start()
        self.mock_waffle_flags.return_value = {
            REJECTED_EXAM_OVERRIDES_GRADE: MockWaffleFlag(True)
        }

    def tearDown(self):
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
        self.assertIsNone(override_obj)

    @freeze_time('2017-01-01')
    def test_undo_override_subsection_grade(self):
        self.service.undo_override_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=self.course.id,
            usage_key_or_id=self.subsection.location,
        )

        override = self.service.get_subsection_grade_override(self.user.id, self.course.id, self.subsection.location)
        self.assertIsNone(override)

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

    def test_should_override_grade_on_rejected_exam(self):
        self.assertTrue(self.service.should_override_grade_on_rejected_exam('course-v1:edX+DemoX+Demo_Course'))
        self.mock_waffle_flags.return_value = {
            REJECTED_EXAM_OVERRIDES_GRADE: MockWaffleFlag(False)
        }
        self.assertFalse(self.service.should_override_grade_on_rejected_exam('course-v1:edX+DemoX+Demo_Course'))
