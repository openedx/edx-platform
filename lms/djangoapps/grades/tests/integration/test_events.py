"""
Test grading events across apps.
"""
# pylint: disable=protected-access

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from lms.djangoapps.instructor.enrollment import reset_student_attempts
from lms.djangoapps.instructor_task.api import submit_rescore_problem_for_student
from mock import patch
from openedx.core.djangolib.testing.utils import get_mock_request
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from courseware.tests.test_submitting_problems import ProblemSubmissionTestMixin
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum

STATE_DELETED_TYPE = 'edx.grades.problem.state_deleted'
RESCORE_TYPE = 'edx.grades.problem.rescored'
SUBMITTED_TYPE = 'edx.grades.problem.submitted'


class GradesEventIntegrationTest(ProblemSubmissionTestMixin, SharedModuleStoreTestCase):
    """
    Tests integration between the eventing in various layers
    of the grading infrastructure.
    """
    @classmethod
    def setUpClass(cls):
        super(GradesEventIntegrationTest, cls).setUpClass()
        cls.store = modulestore()
        with cls.store.default_store(ModuleStoreEnum.Type.split):
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

    def setUp(self):
        super(GradesEventIntegrationTest, self).setUp()
        self.request = get_mock_request(UserFactory())
        self.student = self.request.user
        self.client.login(username=self.student.username, password="test")
        CourseEnrollment.enroll(self.student, self.course.id)
        self.instructor = UserFactory.create(is_staff=True, username=u'test_instructor', password=u'test')
        self.refresh_course()

    @patch('lms.djangoapps.instructor.enrollment.tracker')
    @patch('lms.djangoapps.grades.signals.handlers.tracker')
    @patch('lms.djangoapps.grades.models.tracker')
    def test_delete_student_state_events(self, models_tracker, handlers_tracker, enrollment_tracker):
        # submit answer
        self.submit_question_answer('p1', {'2_1': 'choice_choice_2'})

        # check logging to make sure id's are tracked correctly across events
        event_transaction_id = handlers_tracker.method_calls[0][1][1]['event_transaction_id']
        for call in models_tracker.method_calls:
            self.assertEqual(event_transaction_id, call[1][1]['event_transaction_id'])
            self.assertEqual(unicode(SUBMITTED_TYPE), call[1][1]['event_transaction_type'])

        handlers_tracker.emit.assert_called_with(
            unicode(SUBMITTED_TYPE),
            {
                'user_id': unicode(self.student.id),
                'event_transaction_id': event_transaction_id,
                'event_transaction_type': unicode(SUBMITTED_TYPE),
                'course_id': unicode(self.course.id),
                'problem_id': unicode(self.problem.location),
                'weighted_earned': 2.0,
                'weighted_possible': 2.0,
            }
        )

        course = self.store.get_course(self.course.id, depth=0)
        models_tracker.emit.assert_called_with(
            u'edx.grades.course.grade_calculated',
            {
                'course_version': unicode(course.course_version),
                'percent_grade': 0.02,
                'grading_policy_hash': u'ChVp0lHGQGCevD0t4njna/C44zQ=',
                'user_id': unicode(self.student.id),
                'letter_grade': u'',
                'event_transaction_id': event_transaction_id,
                'event_transaction_type': unicode(SUBMITTED_TYPE),
                'course_id': unicode(self.course.id),
                'course_edited_timestamp': unicode(course.subtree_edited_on),
            }
        )
        models_tracker.reset_mock()
        handlers_tracker.reset_mock()

        # delete state
        reset_student_attempts(self.course.id, self.student, self.problem.location, self.instructor, delete_module=True)

        # check logging to make sure id's are tracked correctly across events
        event_transaction_id = enrollment_tracker.method_calls[0][1][1]['event_transaction_id']

        # make sure the id is propagated throughout the event flow
        for call in models_tracker.method_calls:
            self.assertEqual(event_transaction_id, call[1][1]['event_transaction_id'])
            self.assertEqual(unicode(STATE_DELETED_TYPE), call[1][1]['event_transaction_type'])

        # ensure we do not log a problem submitted event when state is deleted
        handlers_tracker.assert_not_called()
        enrollment_tracker.emit.assert_called_with(
            unicode(STATE_DELETED_TYPE),
            {
                'user_id': unicode(self.student.id),
                'course_id': unicode(self.course.id),
                'problem_id': unicode(self.problem.location),
                'instructor_id': unicode(self.instructor.id),
                'event_transaction_id': event_transaction_id,
                'event_transaction_type': unicode(STATE_DELETED_TYPE),
            }
        )

        course = modulestore().get_course(self.course.id, depth=0)
        models_tracker.emit.assert_called_with(
            u'edx.grades.course.grade_calculated',
            {
                'percent_grade': 0.0,
                'grading_policy_hash': u'ChVp0lHGQGCevD0t4njna/C44zQ=',
                'user_id': unicode(self.student.id),
                'letter_grade': u'',
                'event_transaction_id': event_transaction_id,
                'event_transaction_type': unicode(STATE_DELETED_TYPE),
                'course_id': unicode(self.course.id),
                'course_edited_timestamp': unicode(course.subtree_edited_on),
                'course_version': unicode(course.course_version),
            }
        )
        enrollment_tracker.reset_mock()
        models_tracker.reset_mock()
        handlers_tracker.reset_mock()

    @patch('lms.djangoapps.instructor_task.tasks_helper.tracker')
    @patch('lms.djangoapps.grades.signals.handlers.tracker')
    @patch('lms.djangoapps.grades.models.tracker')
    def test_rescoring_events(self, models_tracker, handlers_tracker, instructor_task_tracker):
        # submit answer
        self.submit_question_answer('p1', {'2_1': 'choice_choice_3'})
        models_tracker.reset_mock()
        handlers_tracker.reset_mock()

        new_problem_xml = MultipleChoiceResponseXMLFactory().build_xml(
            question_text='The correct answer is Choice 3',
            choices=[False, False, False, True],
            choice_names=['choice_0', 'choice_1', 'choice_2', 'choice_3']
        )
        module_store = modulestore()
        with module_store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            self.problem.data = new_problem_xml
            module_store.update_item(self.problem, self.instructor.id)
            module_store.publish(self.problem.location, self.instructor.id)

        submit_rescore_problem_for_student(
            request=get_mock_request(self.instructor),
            usage_key=self.problem.location,
            student=self.student,
            only_if_higher=False
        )
        # check logging to make sure id's are tracked correctly across
        # events
        event_transaction_id = instructor_task_tracker.method_calls[0][1][1]['event_transaction_id']

        # make sure the id is propagated throughout the event flow
        for call in models_tracker.method_calls:
            self.assertEqual(event_transaction_id, call[1][1]['event_transaction_id'])
            self.assertEqual(unicode(RESCORE_TYPE), call[1][1]['event_transaction_type'])

        handlers_tracker.assert_not_called()

        instructor_task_tracker.emit.assert_called_with(
            unicode(RESCORE_TYPE),
            {
                'course_id': unicode(self.course.id),
                'user_id': unicode(self.student.id),
                'problem_id': unicode(self.problem.location),
                'new_weighted_earned': 2,
                'new_weighted_possible': 2,
                'only_if_higher': False,
                'instructor_id': unicode(self.instructor.id),
                'event_transaction_id': event_transaction_id,
                'event_transaction_type': unicode(RESCORE_TYPE),
            }
        )
        course = modulestore().get_course(self.course.id, depth=0)
        models_tracker.emit.assert_called_with(
            u'edx.grades.course.grade_calculated',
            {
                'course_version': unicode(course.course_version),
                'percent_grade': 0.02,
                'grading_policy_hash': u'ChVp0lHGQGCevD0t4njna/C44zQ=',
                'user_id': unicode(self.student.id),
                'letter_grade': u'',
                'event_transaction_id': event_transaction_id,
                'event_transaction_type': unicode(RESCORE_TYPE),
                'course_id': unicode(self.course.id),
                'course_edited_timestamp': unicode(course.subtree_edited_on),
            }
        )
        instructor_task_tracker.reset_mock()
        models_tracker.reset_mock()
        handlers_tracker.reset_mock()
