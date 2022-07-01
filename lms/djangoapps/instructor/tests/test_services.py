"""
Tests for the InstructorService
"""
import json
from unittest import mock

import pytest
from completion.waffle import ENABLE_COMPLETION_TRACKING_SWITCH
from django.core.exceptions import ObjectDoesNotExist
from edx_toggles.toggles.testutils import override_waffle_switch
from opaque_keys import InvalidKeyError

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.instructor.access import allow_access
from lms.djangoapps.instructor.services import InstructorService
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.partitions.partitions import Group, UserPartition  # lint-amnesty, pylint: disable=wrong-import-order


class InstructorServiceTests(SharedModuleStoreTestCase):
    """
    Tests for the InstructorService
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.email = 'escalation@test.com'
        cls.course = CourseFactory.create(proctoring_escalation_email=cls.email)
        cls.section = ItemFactory.create(parent=cls.course, category='chapter')
        cls.subsection = ItemFactory.create(parent=cls.section, category='sequential')
        cls.unit = ItemFactory.create(parent=cls.subsection, category='vertical')
        cls.problem = ItemFactory.create(parent=cls.unit, category='problem')
        cls.unit_2 = ItemFactory.create(parent=cls.subsection, category='vertical')
        cls.problem_2 = ItemFactory.create(parent=cls.unit_2, category='problem')
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
            module_state_key=self.problem.location,
            state=json.dumps({'attempts': 2}),
        )

    @mock.patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    @mock.patch('completion.handlers.BlockCompletion.objects.submit_completion')
    def test_reset_student_attempts_delete(self, mock_submit, _mock_signal):
        """
        Test delete student state.
        """

        # make sure the attempt is there
        assert StudentModule.objects.filter(student=self.module_to_reset.student, course_id=self.course.id,
                                            module_state_key=self.module_to_reset.module_state_key).count() == 1

        with override_waffle_switch(ENABLE_COMPLETION_TRACKING_SWITCH, True):
            self.service.delete_student_attempt(
                self.student.username,
                str(self.course.id),
                str(self.subsection.location),
                requesting_user=self.student,
            )

        # make sure the module has been deleted
        assert StudentModule.objects.filter(student=self.module_to_reset.student, course_id=self.course.id,
                                            module_state_key=self.module_to_reset.module_state_key).count() == 0

        # Assert we send completion == 0.0 for both problems even though the second problem was never viewed
        assert mock_submit.call_count == 2
        mock_submit.assert_any_call(user=self.student, block_key=self.problem.location, completion=0.0)
        mock_submit.assert_any_call(user=self.student, block_key=self.problem_2.location, completion=0.0)

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
            str(self.problem_2.location),
            requesting_user=self.student,
        )
        assert result is None

    @mock.patch('completion.handlers.BlockCompletion.objects.submit_completion')
    def test_complete_student_attempt_success(self, mock_submit):
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

        with override_waffle_switch(ENABLE_COMPLETION_TRACKING_SWITCH, True):
            self.service.complete_student_attempt(self.student.username, str(subsection.location))

        # Only Completable leaf blocks should have completion published
        assert mock_submit.call_count == 2
        mock_submit.assert_any_call(user=self.student, block_key=video.location, completion=1.0)
        mock_submit.assert_any_call(user=self.student, block_key=problem.location, completion=1.0)

    @mock.patch('completion.handlers.BlockCompletion.objects.submit_completion')
    def test_complete_student_attempt_split_test(self, mock_submit):
        """
        Asserts complete_student_attempt correctly publishes completion when a split test is involved

        This test case exists because we ran into a bug about the user_service not existing
        when a split_test existed inside of a subsection. Associated with this change was adding
        in the user state into the module before attempting completion and this ensures that is
        working properly.
        """
        partition = UserPartition(
            0,
            'first_partition',
            'First Partition',
            [
                Group(0, 'alpha'),
                Group(1, 'beta')
            ]
        )
        course = CourseFactory.create(user_partitions=[partition])
        section = ItemFactory.create(parent=course, category='chapter')
        subsection = ItemFactory.create(parent=section, category='sequential')

        c0_url = course.id.make_usage_key('vertical', 'split_test_cond0')
        c1_url = course.id.make_usage_key('vertical', 'split_test_cond1')
        split_test = ItemFactory.create(
            parent=subsection,
            category='split_test',
            user_partition_id=0,
            group_id_to_child={'0': c0_url, '1': c1_url},
        )

        cond0vert = ItemFactory.create(parent=split_test, category='vertical', location=c0_url)
        ItemFactory.create(parent=cond0vert, category='video')
        ItemFactory.create(parent=cond0vert, category='problem')

        cond1vert = ItemFactory.create(parent=split_test, category='vertical', location=c1_url)
        ItemFactory.create(parent=cond1vert, category='video')
        ItemFactory.create(parent=cond1vert, category='html')

        with override_waffle_switch(ENABLE_COMPLETION_TRACKING_SWITCH, True):
            self.service.complete_student_attempt(self.student.username, str(subsection.location))

        # Only the group the user was assigned to should have completion published.
        # Either cond0vert's children or cond1vert's children
        assert mock_submit.call_count == 2

    @mock.patch('lms.djangoapps.instructor.tasks.log.error')
    def test_complete_student_attempt_bad_user(self, mock_logger):
        """
        Assert complete_student_attempt with a bad user raises error and returns None
        """
        username = 'bad_user'
        block_id = str(self.problem.location)
        self.service.complete_student_attempt(username, block_id)
        mock_logger.assert_called_once_with(
            self.complete_error_prefix.format(user=username, content_id=block_id) + 'User does not exist!'
        )

    @mock.patch('lms.djangoapps.instructor.tasks.log.error')
    def test_complete_student_attempt_bad_content_id(self, mock_logger):
        """
        Assert complete_student_attempt with a bad content_id raises error and returns None
        """
        username = self.student.username
        self.service.complete_student_attempt(username, 'foo/bar/baz')
        mock_logger.assert_called_once_with(
            self.complete_error_prefix.format(user=username, content_id='foo/bar/baz') + 'Invalid content_id!'
        )

    @mock.patch('lms.djangoapps.instructor.tasks.log.error')
    def test_complete_student_attempt_nonexisting_item(self, mock_logger):
        """
        Assert complete_student_attempt with nonexisting item in the modulestore
        raises error and returns None
        """
        username = self.student.username
        block = 'i4x://org.0/course_0/problem/fake_problem'
        self.service.complete_student_attempt(username, block)
        mock_logger.assert_called_once_with(
            self.complete_error_prefix.format(user=username, content_id=block) + 'Block not found in the modulestore!'
        )

    @mock.patch('lms.djangoapps.instructor.tasks.log.error')
    def test_complete_student_attempt_failed_module(self, mock_logger):
        """
        Assert complete_student_attempt with failed get_module raises error and returns None
        """
        username = self.student.username
        with mock.patch('lms.djangoapps.instructor.tasks.get_module_for_descriptor', return_value=None):
            self.service.complete_student_attempt(username, str(self.course.location))
        mock_logger.assert_called_once_with(
            self.complete_error_prefix.format(user=username, content_id=self.course.location) +
            'Module unable to be created from descriptor!'
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
