"""
Test for LMS instructor background task queue management
"""
import ddt
from mock import patch, Mock, MagicMock
from nose.plugins.attrib import attr
from bulk_email.models import CourseEmail, SEND_TO_MYSELF, SEND_TO_STAFF, SEND_TO_LEARNERS
from courseware.tests.factories import UserFactory
from xmodule.modulestore.exceptions import ItemNotFoundError

from lms.djangoapps.instructor_task.api import (
    get_running_instructor_tasks,
    get_instructor_task_history,
    submit_rescore_problem_for_all_students,
    submit_rescore_problem_for_student,
    submit_rescore_entrance_exam_for_student,
    submit_reset_problem_attempts_for_all_students,
    submit_reset_problem_attempts_in_entrance_exam,
    submit_delete_problem_state_for_all_students,
    submit_delete_entrance_exam_state_for_student,
    submit_bulk_course_email,
    submit_calculate_problem_responses_csv,
    submit_calculate_students_features_csv,
    submit_cohort_students,
    submit_detailed_enrollment_features_csv,
    submit_calculate_may_enroll_csv,
    submit_executive_summary_report,
    submit_course_survey_report,
    generate_certificates_for_students,
    regenerate_certificates,
    submit_export_ora2_data,
    SpecificStudentIdMissingError,
)

from lms.djangoapps.instructor_task.api_helper import AlreadyRunningError
from lms.djangoapps.instructor_task.models import InstructorTask, PROGRESS
from lms.djangoapps.instructor_task.tasks import export_ora2_data
from lms.djangoapps.instructor_task.tests.test_base import (
    InstructorTaskTestCase,
    InstructorTaskCourseTestCase,
    InstructorTaskModuleTestCase,
    TestReportMixin,
    TEST_COURSE_KEY,
)
from certificates.models import CertificateStatuses, CertificateGenerationHistory


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
        self.assertEquals(set(task_ids), set(progress_task_ids))

    def test_get_instructor_task_history(self):
        # when fetching historical tasks, we get all tasks, including running tasks
        expected_ids = []
        for _ in range(1, 5):
            expected_ids.append(self._create_failure_entry().task_id)
            expected_ids.append(self._create_success_entry().task_id)
            expected_ids.append(self._create_progress_entry().task_id)
        task_ids = [instructor_task.task_id for instructor_task
                    in get_instructor_task_history(TEST_COURSE_KEY, usage_key=self.problem_url)]
        self.assertEquals(set(task_ids), set(expected_ids))
        # make the same call using explicit task_type:
        task_ids = [instructor_task.task_id for instructor_task
                    in get_instructor_task_history(
                        TEST_COURSE_KEY,
                        usage_key=self.problem_url,
                        task_type='rescore_problem'
                    )]
        self.assertEquals(set(task_ids), set(expected_ids))
        # make the same call using a non-existent task_type:
        task_ids = [instructor_task.task_id for instructor_task
                    in get_instructor_task_history(
                        TEST_COURSE_KEY,
                        usage_key=self.problem_url,
                        task_type='dummy_type'
                    )]
        self.assertEquals(set(task_ids), set())


@attr(shard=3)
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

    def _test_submit_with_long_url(self, task_function, student=None):
        problem_url_name = 'x' * 255
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        with self.assertRaises(ValueError):
            if student is not None:
                task_function(self.create_task_request(self.instructor), location, student)
            else:
                task_function(self.create_task_request(self.instructor), location)

    def test_submit_rescore_all_with_long_url(self):
        self._test_submit_with_long_url(submit_rescore_problem_for_all_students)

    def test_submit_rescore_student_with_long_url(self):
        self._test_submit_with_long_url(submit_rescore_problem_for_student, self.student)

    def test_submit_reset_all_with_long_url(self):
        self._test_submit_with_long_url(submit_reset_problem_attempts_for_all_students)

    def test_submit_delete_all_with_long_url(self):
        self._test_submit_with_long_url(submit_delete_problem_state_for_all_students)

    @ddt.data(
        (submit_rescore_problem_for_all_students, 'rescore_problem'),
        (submit_rescore_problem_for_all_students, 'rescore_problem_if_higher', {'only_if_higher': True}),
        (submit_rescore_problem_for_student, 'rescore_problem', {'student': True}),
        (submit_rescore_problem_for_student, 'rescore_problem_if_higher', {'student': True, 'only_if_higher': True}),
        (submit_reset_problem_attempts_for_all_students, 'reset_problem_attempts'),
        (submit_delete_problem_state_for_all_students, 'delete_problem_state'),
        (submit_rescore_entrance_exam_for_student, 'rescore_problem', {'student': True}),
        (
            submit_rescore_entrance_exam_for_student,
            'rescore_problem_if_higher',
            {'student': True, 'only_if_higher': True},
        ),
        (submit_reset_problem_attempts_in_entrance_exam, 'reset_problem_attempts', {'student': True}),
        (submit_delete_entrance_exam_state_for_student, 'delete_problem_state', {'student': True}),
    )
    @ddt.unpack
    def test_submit_task(self, task_function, expected_task_type, params=None):
        if params is None:
            params = {}
        if params.get('student'):
            params['student'] = self.student

        # tests submit, and then tests a second identical submission.
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        instructor_task = task_function(self.create_task_request(self.instructor), location, **params)
        self.assertEquals(instructor_task.task_type, expected_task_type)

        # test resubmitting, by updating the existing record:
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        instructor_task.task_state = PROGRESS
        instructor_task.save()

        with self.assertRaises(AlreadyRunningError):
            task_function(self.create_task_request(self.instructor), location, **params)


@attr(shard=3)
@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
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
            problem_location=''
        )
        self._test_resubmission(api_call)

    def test_submit_calculate_students_features(self):
        api_call = lambda: submit_calculate_students_features_csv(
            self.create_task_request(self.instructor),
            self.course.id,
            features=[]
        )
        self._test_resubmission(api_call)

    def test_submit_enrollment_report_features_csv(self):
        api_call = lambda: submit_detailed_enrollment_features_csv(self.create_task_request(self.instructor),
                                                                   self.course.id)
        self._test_resubmission(api_call)

    def test_submit_executive_summary_report(self):
        api_call = lambda: submit_executive_summary_report(
            self.create_task_request(self.instructor), self.course.id
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
