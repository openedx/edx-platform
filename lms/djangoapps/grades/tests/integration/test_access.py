"""
Test grading with access changes.
"""
# pylint: disable=protected-access

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from lms.djangoapps.course_blocks.api import get_course_blocks
from openedx.core.djangolib.testing.utils import get_mock_request
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from courseware.tests.test_submitting_problems import ProblemSubmissionTestMixin
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum

from ...new.subsection_grade import SubsectionGradeFactory


class GradesAccessIntegrationTest(ProblemSubmissionTestMixin, SharedModuleStoreTestCase):
    """
    Tests integration between grading and block access.
    """
    @classmethod
    def setUpClass(cls):
        super(GradesAccessIntegrationTest, cls).setUpClass()
        cls.store = modulestore()
        cls.course = CourseFactory.create()
        cls.chapter = ItemFactory.create(
            parent=cls.course,
            category="chapter",
            display_name="Test Chapter"
        )
        cls.sequence = ItemFactory.create(
            parent=cls.chapter,
            category='sequential',
            display_name="Test Sequential 1",
            graded=True,
            format="Homework"
        )
        cls.vertical = ItemFactory.create(
            parent=cls.sequence,
            category='vertical',
            display_name='Test Vertical 1'
        )
        problem_xml = MultipleChoiceResponseXMLFactory().build_xml(
            question_text='The correct answer is Choice 2',
            choices=[False, False, True, False],
            choice_names=['choice_0', 'choice_1', 'choice_2', 'choice_3']
        )
        cls.problem = ItemFactory.create(
            parent=cls.vertical,
            category="problem",
            display_name="p1",
            data=problem_xml,
            metadata={'weight': 2}
        )

        cls.problem_2 = ItemFactory.create(
            parent=cls.vertical,
            category="problem",
            display_name="p2",
            data=problem_xml,
            metadata={'weight': 2}
        )

    def setUp(self):
        super(GradesAccessIntegrationTest, self).setUp()
        self.request = get_mock_request(UserFactory())
        self.student = self.request.user
        self.client.login(username=self.student.username, password="test")
        CourseEnrollment.enroll(self.student, self.course.id)
        self.instructor = UserFactory.create(is_staff=True, username=u'test_instructor', password=u'test')
        self.refresh_course()

    def test_subsection_access_changed(self):
        """
        Tests retrieving a subsection grade before and after losing access
        to a block in the subsection.
        """
        # submit answers
        self.submit_question_answer('p1', {'2_1': 'choice_choice_2'})
        self.submit_question_answer('p2', {'2_1': 'choice_choice_2'})

        # check initial subsection grade
        course_structure = get_course_blocks(self.request.user, self.course.location)
        subsection_grade_factory = SubsectionGradeFactory(self.request.user, self.course, course_structure)
        grade = subsection_grade_factory.create(self.sequence, read_only=True)
        self.assertEqual(grade.graded_total.earned, 4.0)
        self.assertEqual(grade.graded_total.possible, 4.0)

        # set a block in the subsection to be visible to staff only
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            problem_2 = self.store.get_item(self.problem_2.location)
            problem_2.visible_to_staff_only = True
            self.store.update_item(problem_2, self.instructor.id)
            self.store.publish(self.course.location, self.instructor.id)
        course_structure = get_course_blocks(self.student, self.course.location)

        # ensure that problem_2 is not accessible for the student
        self.assertNotIn(problem_2.location, course_structure)

        # make sure we can still get the subsection grade
        subsection_grade_factory = SubsectionGradeFactory(self.student, self.course, course_structure)
        grade = subsection_grade_factory.create(self.sequence, read_only=True)
        self.assertEqual(grade.graded_total.earned, 4.0)
        self.assertEqual(grade.graded_total.possible, 4.0)
