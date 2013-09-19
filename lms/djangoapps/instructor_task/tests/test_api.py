"""
Test for LMS instructor background task queue management
"""

from xmodule.modulestore.exceptions import ItemNotFoundError

from courseware.tests.factories import UserFactory

from bulk_email.models import CourseEmail, SEND_TO_ALL
from instructor_task.api import (
    get_running_instructor_tasks,
    get_instructor_task_history,
    submit_rescore_problem_for_all_students,
    submit_rescore_problem_for_student,
    submit_reset_problem_attempts_for_all_students,
    submit_delete_problem_state_for_all_students,
    submit_bulk_course_email,
)

from instructor_task.api_helper import AlreadyRunningError
from instructor_task.models import InstructorTask, PROGRESS
from instructor_task.tests.test_base import (InstructorTaskTestCase,
                                             InstructorTaskCourseTestCase,
                                             InstructorTaskModuleTestCase,
                                             TEST_COURSE_ID)


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
        task_ids = [instructor_task.task_id for instructor_task in get_running_instructor_tasks(TEST_COURSE_ID)]
        self.assertEquals(set(task_ids), set(progress_task_ids))

    def test_get_instructor_task_history(self):
        # when fetching historical tasks, we get all tasks, including running tasks
        expected_ids = []
        for _ in range(1, 5):
            expected_ids.append(self._create_failure_entry().task_id)
            expected_ids.append(self._create_success_entry().task_id)
            expected_ids.append(self._create_progress_entry().task_id)
        task_ids = [instructor_task.task_id for instructor_task
                    in get_instructor_task_history(TEST_COURSE_ID, self.problem_url)]
        self.assertEquals(set(task_ids), set(expected_ids))


class InstructorTaskModuleSubmitTest(InstructorTaskModuleTestCase):
    """Tests API methods that involve the submission of module-based background tasks."""

    def setUp(self):
        self.initialize_course()
        self.student = UserFactory.create(username="student", email="student@edx.org")
        self.instructor = UserFactory.create(username="instructor", email="instructor@edx.org")

    def test_submit_nonexistent_modules(self):
        # confirm that a rescore of a non-existent module returns an exception
        problem_url = InstructorTaskModuleTestCase.problem_location("NonexistentProblem")
        course_id = self.course.id
        request = None
        with self.assertRaises(ItemNotFoundError):
            submit_rescore_problem_for_student(request, course_id, problem_url, self.student)
        with self.assertRaises(ItemNotFoundError):
            submit_rescore_problem_for_all_students(request, course_id, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_reset_problem_attempts_for_all_students(request, course_id, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_delete_problem_state_for_all_students(request, course_id, problem_url)

    def test_submit_nonrescorable_modules(self):
        # confirm that a rescore of an existent but unscorable module returns an exception
        # (Note that it is easier to test a scoreable but non-rescorable module in test_tasks,
        # where we are creating real modules.)
        problem_url = self.problem_section.location.url()
        course_id = self.course.id
        request = None
        with self.assertRaises(NotImplementedError):
            submit_rescore_problem_for_student(request, course_id, problem_url, self.student)
        with self.assertRaises(NotImplementedError):
            submit_rescore_problem_for_all_students(request, course_id, problem_url)

    def _test_submit_with_long_url(self, task_function, student=None):
        problem_url_name = 'x' * 255
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        with self.assertRaises(ValueError):
            if student is not None:
                task_function(self.create_task_request(self.instructor), self.course.id, location, student)
            else:
                task_function(self.create_task_request(self.instructor), self.course.id, location)

    def test_submit_rescore_all_with_long_url(self):
        self._test_submit_with_long_url(submit_rescore_problem_for_all_students)

    def test_submit_rescore_student_with_long_url(self):
        self._test_submit_with_long_url(submit_rescore_problem_for_student, self.student)

    def test_submit_reset_all_with_long_url(self):
        self._test_submit_with_long_url(submit_reset_problem_attempts_for_all_students)

    def test_submit_delete_all_with_long_url(self):
        self._test_submit_with_long_url(submit_delete_problem_state_for_all_students)

    def _test_submit_task(self, task_function, student=None):
        # tests submit, and then tests a second identical submission.
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskModuleTestCase.problem_location(problem_url_name)
        if student is not None:
            instructor_task = task_function(self.create_task_request(self.instructor),
                                            self.course.id, location, student)
        else:
            instructor_task = task_function(self.create_task_request(self.instructor),
                                            self.course.id, location)

        # test resubmitting, by updating the existing record:
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        instructor_task.task_state = PROGRESS
        instructor_task.save()

        with self.assertRaises(AlreadyRunningError):
            if student is not None:
                task_function(self.create_task_request(self.instructor), self.course.id, location, student)
            else:
                task_function(self.create_task_request(self.instructor), self.course.id, location)

    def test_submit_rescore_all(self):
        self._test_submit_task(submit_rescore_problem_for_all_students)

    def test_submit_rescore_student(self):
        self._test_submit_task(submit_rescore_problem_for_student, self.student)

    def test_submit_reset_all(self):
        self._test_submit_task(submit_reset_problem_attempts_for_all_students)

    def test_submit_delete_all(self):
        self._test_submit_task(submit_delete_problem_state_for_all_students)


class InstructorTaskCourseSubmitTest(InstructorTaskCourseTestCase):
    """Tests API methods that involve the submission of course-based background tasks."""

    def setUp(self):
        self.initialize_course()
        self.student = UserFactory.create(username="student", email="student@edx.org")
        self.instructor = UserFactory.create(username="instructor", email="instructor@edx.org")

    def _define_course_email(self):
        course_email = CourseEmail.create(self.course.id, self.instructor, SEND_TO_ALL, "Test Subject", "<p>This is a test message</p>")
        return course_email.id

    def test_submit_bulk_email_all(self):
        email_id = self._define_course_email()
        instructor_task = submit_bulk_course_email(self.create_task_request(self.instructor), self.course.id, email_id)

        # test resubmitting, by updating the existing record:
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        instructor_task.task_state = PROGRESS
        instructor_task.save()

        with self.assertRaises(AlreadyRunningError):
            instructor_task = submit_bulk_course_email(self.create_task_request(self.instructor), self.course.id, email_id)
