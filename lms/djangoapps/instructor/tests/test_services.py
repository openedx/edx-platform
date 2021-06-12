"""
Tests for the InstructorService
"""
import json
from unittest import mock

import pytest
from django.core.exceptions import ObjectDoesNotExist
from opaque_keys import InvalidKeyError

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.instructor.access import allow_access
from lms.djangoapps.instructor.services import InstructorService
from lms.djangoapps.instructor.tests.test_tools import msk_from_problem_urlname
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class InstructorServiceTests(SharedModuleStoreTestCase):
    """
    Tests for the InstructorService
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.email = 'escalation@test.com'
        cls.course = CourseFactory.create(proctoring_escalation_email=cls.email)
        cls.problem_location = msk_from_problem_urlname(
            cls.course.id,
            'robot-some-problem-urlname'
        )
        cls.other_problem_location = msk_from_problem_urlname(
            cls.course.id,
            'robot-some-other_problem-urlname'
        )
        cls.problem_urlname = str(cls.problem_location)
        cls.other_problem_urlname = str(cls.other_problem_location)
        cls.complete_error_prefix = ('Error occurred while attempting to complete student attempt for '
                                     'user {user} for content_id {content_id}. ')

    def setUp(self):
        super().setUp()

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
        assert StudentModule.objects.filter(student=self.module_to_reset.student, course_id=self.course.id,
                                            module_state_key=self.module_to_reset.module_state_key).count() == 1

        self.service.delete_student_attempt(
            self.student.username,
            str(self.course.id),
            self.problem_urlname,
            requesting_user=self.student,
        )

        # make sure the module has been deleted
        assert StudentModule.objects.filter(student=self.module_to_reset.student, course_id=self.course.id,
                                            module_state_key=self.module_to_reset.module_state_key).count() == 0

    def test_reset_bad_content_id(self):
        """
        Negative test of trying to reset attempts with bad content_id
        """

        result = self.service.delete_student_attempt(  # lint-amnesty, pylint: disable=assignment-from-none
            self.student.username,
            str(self.course.id),
            'foo/bar/baz',
            requesting_user=self.student,
        )
        assert result is None

    def test_reset_bad_user(self):
        """
        Negative test of trying to reset attempts with bad user identifier
        """

        result = self.service.delete_student_attempt(  # lint-amnesty, pylint: disable=assignment-from-none
            'bad_student',
            str(self.course.id),
            'foo/bar/baz',
            requesting_user=self.student,
        )
        assert result is None

    def test_reset_non_existing_attempt(self):
        """
        Negative test of trying to reset attempts with bad user identifier
        """

        result = self.service.delete_student_attempt(  # lint-amnesty, pylint: disable=assignment-from-none
            self.student.username,
            str(self.course.id),
            self.other_problem_urlname,
            requesting_user=self.student,
        )
        assert result is None

    # So technically, this mock publish is different than what is hit when running this code
    # in production (lms.djangoapps.courseware.module_render.get_module_system_for_user.publish).
    # I tried to figure out why or a way to force it to be more production like and was unsuccessful,
    # so if anyone figures it out at any point, it would be greatly appreciated if you could update this.
    # I thought it was acceptable because I'm still able to confirm correct behavior of the function
    # and the attempted call, it is just going to the wrong publish spot ¯\_(ツ)_/¯
    @mock.patch('xmodule.x_module.DescriptorSystem.publish')
    def test_complete_student_attempt_success(self, mock_publish):
        """
        Assert complete_student_attempt correctly publishes completion for all
        completable children of the given content_id
        """
        # Section, subsection, and unit are all aggregators and not completable so should
        # not be submitted.
        section = ItemFactory.create(parent=self.course, category='chapter')
        subsection = ItemFactory.create(parent=section, category='sequential')
        unit = ItemFactory.create(parent=subsection, category='vertical')

        # should both be submitted
        video = ItemFactory.create(parent=unit, category='video')
        problem = ItemFactory.create(parent=unit, category='problem')

        # Not a completable block
        ItemFactory.create(parent=unit, category='discussion')

        self.service.complete_student_attempt(self.student.username, str(subsection.location))
        # Only Completable leaf blocks should have completion published
        assert mock_publish.call_count == 2

        # The calls take the form of (xblock, publish_event, publish_data), which in our case
        # will look like (xblock, 'completion', {'completion': 1.0, 'user_id': 1}).
        # I'd prefer to be able to just assert all fields at once, but for some reason the value
        # of the xblock in the mock call and the object above are different (even with a refetch)
        # so I'm settling for just ensuring the location (block_key) of both are identical
        video_call = mock_publish.call_args_list[0][0]
        assert video_call[0].location == video.location
        assert video_call[1] == 'completion'
        assert video_call[2] == {'completion': 1.0, 'user_id': self.student.id}
        problem_call = mock_publish.call_args_list[1][0]
        assert problem_call[0].location == problem.location
        assert problem_call[1] == 'completion'
        assert problem_call[2] == {'completion': 1.0, 'user_id': self.student.id}

    @mock.patch('lms.djangoapps.instructor.services.log.error')
    def test_complete_student_attempt_bad_user(self, mock_logger):
        """
        Assert complete_student_attempt with a bad user raises error and returns None
        """
        username = 'bad_user'
        self.service.complete_student_attempt(username, self.problem_urlname)
        mock_logger.assert_called_once_with(
            self.complete_error_prefix.format(user=username, content_id=self.problem_urlname) + 'User does not exist!'
        )

    @mock.patch('lms.djangoapps.instructor.services.log.error')
    def test_complete_student_attempt_bad_content_id(self, mock_logger):
        """
        Assert complete_student_attempt with a bad content_id raises error and returns None
        """
        username = self.student.username
        self.service.complete_student_attempt(username, 'foo/bar/baz')
        mock_logger.assert_called_once_with(
            self.complete_error_prefix.format(user=username, content_id='foo/bar/baz') + 'Invalid content_id!'
        )

    @mock.patch('lms.djangoapps.instructor.services.log.error')
    def test_complete_student_attempt_nonexisting_item(self, mock_logger):
        """
        Assert complete_student_attempt with nonexisting item in the modulestore
        raises error and returns None
        """
        username = self.student.username
        block = self.problem_urlname
        self.service.complete_student_attempt(username, block)
        mock_logger.assert_called_once_with(
            self.complete_error_prefix.format(user=username, content_id=block) + 'Block not found in the modulestore!'
        )

    def test_is_user_staff(self):
        """
        Test to assert that the user is staff or not
        """
        result = self.service.is_course_staff(
            self.student,
            str(self.course.id)
        )
        assert not result

        # allow staff access to the student
        allow_access(self.course, self.student, 'staff')
        result = self.service.is_course_staff(
            self.student,
            str(self.course.id)
        )
        assert result

    def test_report_suspicious_attempt(self):
        """
        Test to verify that the create_zendesk_ticket() is called
        """
        requester_name = "edx-proctoring"
        email = "edx-proctoring@edx.org"
        subject = "Proctored Exam Review: {review_status}".format(review_status="Suspicious")

        body = "A proctored exam attempt for {exam_name} in {course_name} by username: {student_username} was " \
               "reviewed as {review_status} by the proctored exam review provider.\n" \
               "Review link: {url}"
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
                course_id=str(self.course.id),
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
                course_id=str(self.course.id),
                exam_name=args['exam_name'],
                student_username=args["student_username"],
                review_status="Suspicious",
                review_url=args['url'],
            )
        expected_body = body.format(**args)
        mock_create_zendesk_ticket.assert_called_with(requester_name, email, subject, expected_body, tags)

    def test_get_proctoring_escalation_email_from_course_key(self):
        """
        Test that it returns the correct proctoring escalation email from a course key object
        """
        email = self.service.get_proctoring_escalation_email(self.course.id)
        assert email == self.email

    def test_get_proctoring_escalation_email_from_course_id(self):
        """
        Test that it returns the correct proctoring escalation email from a course id string
        """
        email = self.service.get_proctoring_escalation_email(str(self.course.id))
        assert email == self.email

    def test_get_proctoring_escalation_email_no_course(self):
        """
        Test that it raises an exception if the course is not found
        """
        with pytest.raises(ObjectDoesNotExist):
            self.service.get_proctoring_escalation_email('a/b/c')

    def test_get_proctoring_escalation_email_invalid_key(self):
        """
        Test that it raises an exception if the course_key is invalid
        """
        with pytest.raises(InvalidKeyError):
            self.service.get_proctoring_escalation_email('invalid key')
