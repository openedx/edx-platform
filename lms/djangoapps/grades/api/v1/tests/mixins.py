"""
Mixins classes being used by all test classes within this folder
"""
from datetime import datetime

from pytz import UTC

from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE


class GradeViewTestMixin(SharedModuleStoreTestCase):
    """
    Mixin class for grades related view tests
    The following tests assume that the grading policy is the edX default one:
    {
        "GRADER": [
            {
                "drop_count": 2,
                "min_count": 12,
                "short_label": "HW",
                "type": "Homework",
                "weight": 0.15
            },
            {
                "drop_count": 2,
                "min_count": 12,
                "type": "Lab",
                "weight": 0.15
            },
            {
                "drop_count": 0,
                "min_count": 1,
                "short_label": "Midterm",
                "type": "Midterm Exam",
                "weight": 0.3
            },
            {
                "drop_count": 0,
                "min_count": 1,
                "short_label": "Final",
                "type": "Final Exam",
                "weight": 0.4
            }
        ],
        "GRADE_CUTOFFS": {
            "Pass": 0.5
        }
    }
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(GradeViewTestMixin, cls).setUpClass()

        cls.course = cls._create_test_course_with_default_grading_policy(
            display_name='test course', run="Testing_course"
        )
        cls.empty_course = cls._create_test_course_with_default_grading_policy(
            display_name='empty test course', run="Empty_testing_course"
        )
        cls.course_key = cls.course.id

    def _create_user_enrollments(self, *users):
        date = datetime(2013, 1, 22, tzinfo=UTC)
        for user in users:
            CourseEnrollmentFactory(
                course_id=self.course.id,
                user=user,
                created=date,
            )

    def setUp(self):
        super(GradeViewTestMixin, self).setUp()
        self.password = 'test'
        self.global_staff = GlobalStaffFactory.create()
        self.student = UserFactory(password=self.password, username='student')
        self.other_student = UserFactory(password=self.password, username='other_student')
        self._create_user_enrollments(self.student, self.other_student)

    @classmethod
    def _create_test_course_with_default_grading_policy(cls, display_name, run):
        """
        Utility method to create a course with a default grading policy
        """
        course = CourseFactory.create(display_name=display_name, run=run)
        _ = CourseOverviewFactory.create(id=course.id)

        chapter = ItemFactory.create(
            category='chapter',
            parent_location=course.location,
            display_name="Chapter 1",
        )
        # create a problem for each type and minimum count needed by the grading policy
        # A section is not considered if the student answers less than "min_count" problems
        for grading_type, min_count in (("Homework", 12), ("Lab", 12), ("Midterm Exam", 1), ("Final Exam", 1)):
            for num in xrange(min_count):
                section = ItemFactory.create(
                    category='sequential',
                    parent_location=chapter.location,
                    due=datetime(2017, 12, 18, 11, 30, 00),
                    display_name='Sequential {} {}'.format(grading_type, num),
                    format=grading_type,
                    graded=True,
                )
                vertical = ItemFactory.create(
                    category='vertical',
                    parent_location=section.location,
                    display_name='Vertical {} {}'.format(grading_type, num),
                )
                ItemFactory.create(
                    category='problem',
                    parent_location=vertical.location,
                    display_name='Problem {} {}'.format(grading_type, num),
                )

        return course
