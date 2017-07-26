import ddt
from lms.djangoapps.grades.models import PersistentSubsectionGrade, PersistentSubsectionGradeOverride
from lms.djangoapps.grades.services import GradesService, _get_key
from opaque_keys.edx.keys import CourseKey, UsageKey
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


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

    def test_get_subsection_grade(self):
        self.assertDictEqual(self.service.get_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=self.course.id,
            usage_key_or_id=self.subsection.location
        ), {
            'earned_all': 6.0,
            'earned_graded': 5.0
        })

        # test with id strings as parameters instead
        self.assertDictEqual(self.service.get_subsection_grade(
            user_id=self.user.id,
            course_key_or_id=str(self.course.id),
            usage_key_or_id=str(self.subsection.location)
        ), {
            'earned_all': 6.0,
            'earned_graded': 5.0
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

        grade = PersistentSubsectionGrade.objects.get(
            user_id=self.user.id,
            course_id=self.course.id,
            usage_key=self.subsection.location
        )

        self.assertEqual(grade.earned_all, expected['earned_all'])
        self.assertEqual(grade.earned_graded, expected['earned_graded'])

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
