"""
Test for LMS instructor background task queue management
"""


import ddt
from celery.states import FAILURE
from mock import MagicMock, Mock, patch
from six.moves import range

from lms.djangoapps.bulk_email.models import SEND_TO_LEARNERS, SEND_TO_MYSELF, SEND_TO_STAFF, CourseEmail
from common.test.utils import normalize_repr
from lms.djangoapps.courseware.tests.factories import UserFactory
from lms.djangoapps.certificates.models import CertificateGenerationHistory, CertificateStatuses
from lms.djangoapps.instructor_task.api import (
    SpecificStudentIdMissingError,
    generate_certificates_for_students,
    get_instructor_task_history,
    get_running_instructor_tasks,
    regenerate_certificates,
    submit_bulk_course_email,
    submit_calculate_may_enroll_csv,
    submit_calculate_problem_responses_csv,
    submit_calculate_students_features_csv,
    submit_cohort_students,
    submit_course_survey_report,
    submit_delete_entrance_exam_state_for_student,
    submit_delete_problem_state_for_all_students,
    submit_export_ora2_data,
    submit_export_ora2_submission_files,
    submit_override_score,
    submit_rescore_entrance_exam_for_student,
    submit_rescore_problem_for_all_students,
    submit_rescore_problem_for_student,
    submit_reset_problem_attempts_for_all_students,
    submit_reset_problem_attempts_in_entrance_exam
)
from lms.djangoapps.instructor_task.api_helper import AlreadyRunningError, QueueConnectionError
from lms.djangoapps.instructor_task.models import PROGRESS, InstructorTask
from lms.djangoapps.instructor_task.tasks import export_ora2_data, export_ora2_submission_files
from lms.djangoapps.instructor_task.tests.test_base import (
    TEST_COURSE_KEY,
    InstructorTaskCourseTestCase,
    InstructorTaskModuleTestCase,
    InstructorTaskTestCase,
    TestReportMixin
)
from xmodule.modulestore.exceptions import ItemNotFoundError


class InstructorTaskReportTest(InstructorTaskTestCase):
    """
    Tests API methods that involve the reporting of status for background tasks.
    """

    def test_get_running_instructor_tasks(self):
        # when fetching running tasks, we get all running tasks, and only running tasks
        for _ in range(1, 5):
            self._create_failure_entry()
            self._create_success_entry()
        progress_task_ids = [self._create_progress_entry().task_id for _ in range(1, 5)]
        task_ids = [instructor_task.task_id for instructor_task in get_running_instructor_tasks(TEST_COURSE_KEY)]
        self.assertEqual(set(task_ids), set(progress_task_ids))

    def test_get_instructor_task_history(self):
        # when fetching historical tasks, we get all tasks, including running tasks
        expected_ids = []
        for _ in range(1, 5):
            expected_ids.append(self._create_failure_entry().task_id)
            expected_ids.append(self._create_success_entry().task_id)
            expected_ids.append(self._create_progress_entry().task_id)
        task_ids = [instructor_task.task_id for instructor_task
                    in get_instructor_task_history(TEST_COURSE_KEY, usage_key=self.problem_url)]
        self.assertEqual(set(task_ids), set(expected_ids))
        # make the same call using explicit task_type:
        task_ids = [instructor_task.task_id for instructor_task
                    in get_instructor_task_history(
                        TEST_COURSE_KEY,
                        usage_key=self.problem_url,
                        task_type='rescore_problem'
                    )]
        self.assertEqual(set(task_ids), set(expected_ids))
        # make the same call using a non-existent task_type:
        task_ids = [instructor_task.task_id for instructor_task
                    in get_instructor_task_history(
                        TEST_COURSE_KEY,
                        usage_key=self.problem_url,
                        task_type='dummy_type'
                    )]
        self.assertEqual(set(task_ids), set())


@ddt.ddt
class InstructorTaskModuleSubmitTest(InstructorTaskModuleTestCase):
    """Tests API methods that involve the submission of module-based background tasks."""

    def setUp(self):
        super(InstructorTaskModuleSubmitTest, self).setUp()

        self.initialize_course()
        self.student = UserFactory.create(username="student", email="student@edx.org")
        self.instructor = UserFactory.create(username="instructor", email="instructor@edx.org")

    def test_submit_nonexistent_modules(self):
        # confirm that a rescore of a non-existent module returns an exception
        problem_url = InstructorTaskModuleTestCase.problem_location("NonexistentProblem")
        request = None
        with self.assertRaises(ItemNotFoundError):
            submit_rescore_problem_for_student(request, problem_url, self.student)
        with self.assertRaises(ItemNotFoundError):
            submit_rescore_problem_for_all_students(request, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_reset_problem_attempts_for_all_students(request, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_delete_problem_state_for_all_students(request, problem_url)

    def test_submit_nonrescorable_modules(self):
        # confirm that a rescore of an existent but unscorable module returns an exception
        # (Note that it is easier to test a scoreable but non-rescorable module in test_tasks,
        # where we are creating real modules.)
        problem_url = self.problem_section.location
        request = None
        with self.assertRaises(NotImplementedError):
            submit_rescore_problem_for_student(request, problem_url, self.student)
        with self.assertRaises(NotImplementedError):
            submit_rescore_problem_for_all_students(request, problem_url)

    @ddt.data(
        (normalize_repr(submit_rescore_problem_for_all_students), 'rescore_problem'),
        (
            normalize_repr(submit_rescore_problem_for_all_students),
            'rescore_problem_if_higher',
            {'only_if_higher': True}
        ),
        (normalize_repr(submit_rescore_problem_for_student), 'rescore_problem', {'student': True}),
        (
            normalize_repr(submit_rescore_problem_for_student),
            'rescore_problem_if_higher',
            {'student': True, 'only_if_higher': True}
        ),
        (normalize_repr(submit_reset_problem_attempts_for_all_students), 'reset_problem_attempts'),
        (normalize_repr(submit_delete_problem_state_for_all_students), 'delete_problem_state'),
        (normalize_repr(submit_rescore_entrance_exam_for_student), 'rescore_problem', {'student': True}),
        (
            normalize_repr(submit_rescore_entrance_exam_for_student),
            'rescore_problem_if_higher',
            {'student': True, 'only_if_higher': True},
        ),
        (normalize_repr(submit_reset_problem_attempts_in_entrance_exam), 'reset_problem_attempts', {'student': True}),
        (normalize_repr(submit_delete_entrance_exam_state_for_student), 'delete_problem_state', {'student': True}),
        (normalize_repr(submit_override_score), 'override_problem_score', {'student': True, 'score': 0})
    )
    @ddt.unpack
    def test_submit_task(self, task_function, expected_task_type, params=None):
        """
        Tests submission of instructor task.
        """
        if params is None:
            params = {}
        if params.get('student'):
            params['student'] = self.student

        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)

        # unsuccessful submission, exception raised while submitting.
        with patch('lms.djangoapps.instructor_task.tasks_base.BaseInstructorTask.apply_async') as apply_async:

            error = Exception()
            apply_async.side_effect = error

            with self.assertRaises(QueueConnectionError):
                instructor_task = task_function(self.create_task_request(self.instructor), location, **params)

            most_recent_task = InstructorTask.objects.latest('id')
            self.assertEqual(most_recent_task.task_state, FAILURE)

        # successful submission
        instructor_task = task_function(self.create_task_request(self.instructor), location, **params)
        self.assertEqual(instructor_task.task_type, expected_task_type)

        # test resubmitting, by updating the existing record:
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        instructor_task.task_state = PROGRESS
        instructor_task.save()

        with self.assertRaises(AlreadyRunningError):
            task_function(self.create_task_request(self.instructor), location, **params)


@patch('lms.djangoapps.bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class InstructorTaskCourseSubmitTest(TestReportMixin, InstructorTaskCourseTestCase):
    """Tests API methods that involve the submission of course-based background tasks."""

    def setUp(self):
        super(InstructorTaskCourseSubmitTest, self).setUp()

        self.initialize_course()
        self.student = UserFactory.create(username="student", email="student@edx.org")
        self.instructor = UserFactory.create(username="instructor", email="instructor@edx.org")

    def _define_course_email(self):
        """Create CourseEmail object for testing."""
        course_email = CourseEmail.create(
            self.course.id,
            self.instructor,
            [SEND_TO_MYSELF, SEND_TO_STAFF, SEND_TO_LEARNERS],
            "Test Subject",
            "<p>This is a test message</p>"
        )
        return course_email.id

    def _test_resubmission(self, api_call):
        """
        Tests the resubmission of an instructor task through the API.
        The call to the API is a lambda expression passed via
        `api_call`.  Expects that the API call returns the resulting
        InstructorTask object, and that its resubmission raises
        `AlreadyRunningError`.
        """
        instructor_task = api_call()
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        instructor_task.task_state = PROGRESS
        instructor_task.save()
        with self.assertRaises(AlreadyRunningError):
            api_call()

    def test_submit_bulk_email_all(self):
        email_id = self._define_course_email()
        api_call = lambda: submit_bulk_course_email(
            self.create_task_request(self.instructor),
            self.course.id,
            email_id
        )
        self._test_resubmission(api_call)

    def test_submit_calculate_problem_responses(self):
        api_call = lambda: submit_calculate_problem_responses_csv(
            self.create_task_request(self.instructor),
            self.course.id,
            problem_locations='',
        )
        self._test_resubmission(api_call)

    def test_submit_calculate_students_features(self):
        api_call = lambda: submit_calculate_students_features_csv(
            self.create_task_request(self.instructor),
            self.course.id,
            features=[]
        )
        self._test_resubmission(api_call)

    def test_submit_course_survey_report(self):
        api_call = lambda: submit_course_survey_report(
            self.create_task_request(self.instructor), self.course.id
        )
        self._test_resubmission(api_call)

    def test_submit_calculate_may_enroll(self):
        api_call = lambda: submit_calculate_may_enroll_csv(
            self.create_task_request(self.instructor),
            self.course.id,
            features=[]
        )
        self._test_resubmission(api_call)

    def test_submit_cohort_students(self):
        api_call = lambda: submit_cohort_students(
            self.create_task_request(self.instructor),
            self.course.id,
            file_name=u'filename.csv'
        )
        self._test_resubmission(api_call)

    def test_submit_ora2_request_task(self):
        request = self.create_task_request(self.instructor)

        with patch('lms.djangoapps.instructor_task.api.submit_task') as mock_submit_task:
            mock_submit_task.return_value = MagicMock()
            submit_export_ora2_data(request, self.course.id)

            mock_submit_task.assert_called_once_with(
                request, 'export_ora2_data', export_ora2_data, self.course.id, {}, '')

    def test_submit_export_ora2_submission_files(self):
        request = self.create_task_request(self.instructor)

        with patch('lms.djangoapps.instructor_task.api.submit_task') as mock_submit_task:
            mock_submit_task.return_value = MagicMock()
            submit_export_ora2_submission_files(request, self.course.id)

            mock_submit_task.assert_called_once_with(
                request,
                'export_ora2_submission_files',
                export_ora2_submission_files,
                self.course.id,
                {},
                ''
            )

    def test_submit_generate_certs_students(self):
        """
        Tests certificates generation task submission api
        """
        api_call = lambda: generate_certificates_for_students(
            self.create_task_request(self.instructor),
            self.course.id
        )
        self._test_resubmission(api_call)

    def test_regenerate_certificates(self):
        """
        Tests certificates regeneration task submission api
        """
        def api_call():
            """
            wrapper method for regenerate_certificates
            """
            return regenerate_certificates(
                self.create_task_request(self.instructor),
                self.course.id,
                [CertificateStatuses.downloadable, CertificateStatuses.generating]
            )
        self._test_resubmission(api_call)

    def test_certificate_generation_no_specific_student_id(self):
        """
        Raises ValueError when student_set is 'specific_student' and 'specific_student_id' is None.
        """
        with self.assertRaises(SpecificStudentIdMissingError):
            generate_certificates_for_students(
                self.create_task_request(self.instructor),
                self.course.id,
                student_set='specific_student',
                specific_student_id=None
            )

    def test_certificate_generation_history(self):
        """
        Tests that a new record is added whenever certificate generation/regeneration task is submitted.
        """
        instructor_task = generate_certificates_for_students(
            self.create_task_request(self.instructor),
            self.course.id
        )
        certificate_generation_history = CertificateGenerationHistory.objects.filter(
            course_id=self.course.id,
            generated_by=self.instructor,
            instructor_task=instructor_task,
            is_regeneration=False
        )

        # Validate that record was added to CertificateGenerationHistory
        self.assertTrue(certificate_generation_history.exists())

        instructor_task = regenerate_certificates(
            self.create_task_request(self.instructor),
            self.course.id,
            [CertificateStatuses.downloadable, CertificateStatuses.generating]
        )
        certificate_generation_history = CertificateGenerationHistory.objects.filter(
            course_id=self.course.id,
            generated_by=self.instructor,
            instructor_task=instructor_task,
            is_regeneration=True
        )

        # Validate that record was added to CertificateGenerationHistory
        self.assertTrue(certificate_generation_history.exists())
