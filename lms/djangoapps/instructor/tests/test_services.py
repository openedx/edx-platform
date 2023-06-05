"""
Tests for the InstructorService
"""


import json

import mock
import six

from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.instructor.access import allow_access
from lms.djangoapps.instructor.services import InstructorService
from lms.djangoapps.instructor.tests.test_tools import msk_from_problem_urlname
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class InstructorServiceTests(SharedModuleStoreTestCase):
    """
    Tests for the InstructorService
    """

    @classmethod
    def setUpClass(cls):
        super(InstructorServiceTests, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.problem_location = msk_from_problem_urlname(
            cls.course.id,
            'robot-some-problem-urlname'
        )
        cls.other_problem_location = msk_from_problem_urlname(
            cls.course.id,
            'robot-some-other_problem-urlname'
        )
        cls.problem_urlname = six.text_type(cls.problem_location)
        cls.other_problem_urlname = six.text_type(cls.other_problem_location)

    def setUp(self):
        super(InstructorServiceTests, self).setUp()

        self.student = UserFactory()
        CourseEnrollment.enroll(self.student, self.course.id)

        self.service = InstructorService()
        self.module_to_reset = StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=self.problem_location,
            state=json.dumps({'attempts': 2}),
        )

    @mock.patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_reset_student_attempts_delete(self, _mock_signal):
        """
        Test delete student state.
        """

        # make sure the attempt is there
        self.assertEqual(
            StudentModule.objects.filter(
                student=self.module_to_reset.student,
                course_id=self.course.id,
                module_state_key=self.module_to_reset.module_state_key,
            ).count(),
            1
        )

        self.service.delete_student_attempt(
            self.student.username,
            six.text_type(self.course.id),
            self.problem_urlname,
            requesting_user=self.student,
        )

        # make sure the module has been deleted
        self.assertEqual(
            StudentModule.objects.filter(
                student=self.module_to_reset.student,
                course_id=self.course.id,
                module_state_key=self.module_to_reset.module_state_key,
            ).count(),
            0
        )

    def test_reset_bad_content_id(self):
        """
        Negative test of trying to reset attempts with bad content_id
        """

        result = self.service.delete_student_attempt(
            self.student.username,
            six.text_type(self.course.id),
            'foo/bar/baz',
            requesting_user=self.student,
        )
        self.assertIsNone(result)

    def test_reset_bad_user(self):
        """
        Negative test of trying to reset attempts with bad user identifier
        """

        result = self.service.delete_student_attempt(
            'bad_student',
            six.text_type(self.course.id),
            'foo/bar/baz',
            requesting_user=self.student,
        )
        self.assertIsNone(result)

    def test_reset_non_existing_attempt(self):
        """
        Negative test of trying to reset attempts with bad user identifier
        """

        result = self.service.delete_student_attempt(
            self.student.username,
            six.text_type(self.course.id),
            self.other_problem_urlname,
            requesting_user=self.student,
        )
        self.assertIsNone(result)

    def test_is_user_staff(self):
        """
        Test to assert that the user is staff or not
        """
        result = self.service.is_course_staff(
            self.student,
            six.text_type(self.course.id)
        )
        self.assertFalse(result)

        # allow staff access to the student
        allow_access(self.course, self.student, 'staff')
        result = self.service.is_course_staff(
            self.student,
            six.text_type(self.course.id)
        )
        self.assertTrue(result)

    def test_report_suspicious_attempt(self):
        """
        Test to verify that the create_zendesk_ticket() is called
        """
        requester_name = "edx-proctoring"
        email = "edx-proctoring@edx.org"
        subject = u"Proctored Exam Review: {review_status}".format(review_status="Suspicious")

        body = u"A proctored exam attempt for {exam_name} in {course_name} by username: {student_username} was " \
               u"reviewed as {review_status} by the proctored exam review provider.\n" \
               u"Review link: {url}"
        args = {
            'exam_name': 'test_exam',
            'student_username': 'test_student',
            'url': 'not available',
            'course_name': self.course.display_name,
            'review_status': 'Suspicious',
        }
        expected_body = body.format(**args)
        tags = ["proctoring"]

        with mock.patch("lms.djangoapps.instructor.services.create_zendesk_ticket") as mock_create_zendesk_ticket:
            self.service.send_support_notification(
                course_id=six.text_type(self.course.id),
                exam_name=args['exam_name'],
                student_username=args["student_username"],
                review_status="Suspicious",
                review_url=None,
            )

        mock_create_zendesk_ticket.assert_called_with(requester_name, email, subject, expected_body, tags)
        # Now check sending a notification with a review link
        args['url'] = 'http://review/url'
        with mock.patch("lms.djangoapps.instructor.services.create_zendesk_ticket") as mock_create_zendesk_ticket:
            self.service.send_support_notification(
                course_id=six.text_type(self.course.id),
                exam_name=args['exam_name'],
                student_username=args["student_username"],
                review_status="Suspicious",
                review_url=args['url'],
            )
        expected_body = body.format(**args)
        mock_create_zendesk_ticket.assert_called_with(requester_name, email, subject, expected_body, tags)
