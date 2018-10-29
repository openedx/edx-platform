"""
Test audit user's access to various content based on content-gating features.
"""

from courseware.access import has_access
from course_modes.models import CourseMode

from student.tests.factories import AdminFactory, CourseEnrollmentFactory, UserFactory

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

class TestProblemTypeAccess(ModuleStoreTestCase):

    def setUp(self):
        super(TestProblemTypeAccess, self).setUp()
        self.course = CourseFactory.create(run='testcourse1', display_name="Test Course Title")
        self.audit_user = UserFactory.create()
        self.enrollment = CourseEnrollmentFactory.create(user=self.audit_user, course_id=self.course.id,  mode=CourseMode.AUDIT)
        self.course = CourseFactory.create(run='testcourse1', display_name="Test Course Title")
        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(
                parent=self.course,
                display_name='Overview'
            )
            self.welcome = ItemFactory.create(
                parent=self.chapter,
                display_name='Welcome'
            )
            ItemFactory.create(
                parent=self.course,
                category='chapter',
                display_name="Week 1"
            )
            self.chapter_subsection = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name="Lesson 1"
            )
            chapter_vertical = ItemFactory.create(
                parent=self.chapter_subsection,
                category='vertical',
                display_name='Lesson 1 Vertical - Unit 1'
            )
            self.problem = ItemFactory.create(
                parent=chapter_vertical,
                category="problem",
                display_name="Problem - Unit 1 Problem 1",
                graded=True,
            )


    def test_audit_fails_access_graded_problems(self):
        self.assertTrue(has_access(self.audit_user, 'load', self.problem, course_key=self.course.id).has_access)
