# -*- coding: utf-8 -*-
"""
Unit tests for sending course email
"""
import json
import ddt
from markupsafe import escape
from mock import patch, Mock
from nose.plugins.attrib import attr
import os
from unittest import skipIf

from django.core import mail
from django.core.mail.message import forbid_multi_line_headers
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.test.utils import override_settings

from bulk_email.models import Optout, BulkEmailFlag, CourseEmail, SEND_TO_MYSELF
from bulk_email.tasks import _get_source_address, _get_course_email_context, perform_delegate_email_batches
from openedx.core.djangoapps.course_groups.models import CourseCohort
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from courseware.tests.factories import StaffFactory, InstructorFactory
from instructor_task.models import InstructorTask
from instructor_task.subtasks import update_subtask_status
from student.roles import CourseStaffRole
from student.models import CourseEnrollment
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

STAFF_COUNT = 3
STUDENT_COUNT = 10
LARGE_NUM_EMAILS = 137


class MockCourseEmailResult(object):
    """
    A small closure-like class to keep count of emails sent over all tasks, recorded
    by mock object side effects
    """
    emails_sent = 0

    def get_mock_update_subtask_status(self):
        """Wrapper for mock email function."""
        def mock_update_subtask_status(entry_id, current_task_id, new_subtask_status):
            """Increments count of number of emails sent."""
            self.emails_sent += new_subtask_status.succeeded
            return update_subtask_status(entry_id, current_task_id, new_subtask_status)
        return mock_update_subtask_status


class EmailSendFromDashboardTestCase(SharedModuleStoreTestCase):
    """
    Test that emails send correctly.
    """

    def create_staff_and_instructor(self):
        """
        Creates one instructor and several course staff for self.course. Assigns
        them to self.instructor (single user) and self.staff (list of users),
        respectively.
        """
        self.instructor = InstructorFactory(course_key=self.course.id)

        self.staff = [
            StaffFactory(course_key=self.course.id) for __ in xrange(STAFF_COUNT)
        ]

    def create_students(self):
        """
        Creates users and enrolls them in self.course. Assigns these users to
        self.students.
        """
        self.students = [UserFactory() for _ in xrange(STUDENT_COUNT)]
        for student in self.students:
            CourseEnrollmentFactory.create(user=student, course_id=self.course.id)

    def login_as_user(self, user):
        """
        Log in self.client as user.
        """
        self.client.login(username=user.username, password="test")

    def goto_instructor_dash_email_view(self):
        """
        Goes to the instructor dashboard to verify that the email section is
        there.
        """
        url = reverse('instructor_dashboard', kwargs={'course_id': unicode(self.course.id)})
        # Response loads the whole instructor dashboard, so no need to explicitly
        # navigate to a particular email section
        response = self.client.get(url)
        email_section = '<div class="vert-left send-email" id="section-send-email">'
        # If this fails, it is likely because BulkEmailFlag.is_enabled() is set to False
        self.assertIn(email_section, response.content)

    @classmethod
    def setUpClass(cls):
        super(EmailSendFromDashboardTestCase, cls).setUpClass()
        course_title = u"ẗëṡẗ title ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ"
        cls.course = CourseFactory.create(
            display_name=course_title,
            default_store=ModuleStoreEnum.Type.split
        )

    def setUp(self):
        super(EmailSendFromDashboardTestCase, self).setUp()
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)
        self.create_staff_and_instructor()
        self.create_students()

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")

        self.login_as_user(self.instructor)

        # Pulling up the instructor dash email view here allows us to test sending emails in tests
        self.goto_instructor_dash_email_view()
        self.send_mail_url = reverse(
            'send_email', kwargs={'course_id': unicode(self.course.id)}
        )
        self.success_content = {
            'course_id': unicode(self.course.id),
            'success': True,
        }

    def tearDown(self):
        super(EmailSendFromDashboardTestCase, self).tearDown()
        BulkEmailFlag.objects.all().delete()


@attr('shard_1')
@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestEmailSendFromDashboardMockedHtmlToText(EmailSendFromDashboardTestCase):
    """
    Tests email sending with mocked html_to_text.
    """
    def test_email_disabled(self):
        """
        Test response when email is disabled for course.
        """
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=True)
        test_email = {
            'action': 'Send email',
            'send_to': '["myself"]',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        response = self.client.post(self.send_mail_url, test_email)
        # We should get back a HttpResponseForbidden (status code 403)
        self.assertContains(response, "Email is not enabled for this course.", status_code=403)

    @patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
    def test_send_to_self(self):
        """
        Make sure email send to myself goes to myself.
        """
        test_email = {
            'action': 'send',
            'send_to': '["myself"]',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        # Check that outbox is as expected
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEquals(mail.outbox[0].to[0], self.instructor.email)
        self.assertEquals(mail.outbox[0].subject, 'test subject for myself')
        self.assertEquals(
            mail.outbox[0].from_email,
            u'"{course_display_name}" Course Staff <{course_name}-no-reply@example.com>'.format(
                course_display_name=self.course.display_name,
                course_name=self.course.id.course
            )
        )

    def test_send_to_staff(self):
        """
        Make sure email send to staff and instructors goes there.
        """
        test_email = {
            'action': 'Send email',
            'send_to': '["staff"]',
            'subject': 'test subject for staff',
            'message': 'test message for subject'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        # the 1 is for the instructor in this test and others
        self.assertEquals(len(mail.outbox), 1 + len(self.staff))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff]
        )

    def test_send_to_cohort(self):
        """
        Make sure email sent to a cohort goes there.
        """
        cohort = CourseCohort.create(cohort_name='test cohort', course_id=self.course.id)
        for student in self.students:
            add_user_to_cohort(cohort.course_user_group, student.username)
        test_email = {
            'action': 'Send email',
            'send_to': '["cohort:{}"]'.format(cohort.course_user_group.name),
            'subject': 'test subject for cohort',
            'message': 'test message for cohort'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [s.email for s in self.students]
        )

    def test_send_to_cohort_unenrolled(self):
        """
        Make sure email sent to a cohort does not go to unenrolled members of the cohort.
        """
        self.students.append(UserFactory())  # user will be added to cohort, but not enrolled in course
        cohort = CourseCohort.create(cohort_name='test cohort', course_id=self.course.id)
        for student in self.students:
            add_user_to_cohort(cohort.course_user_group, student.username)
        test_email = {
            'action': 'Send email',
            'send_to': '["cohort:{}"]'.format(cohort.course_user_group.name),
            'subject': 'test subject for cohort',
            'message': 'test message for cohort'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(len(mail.outbox), len(self.students) - 1)
        self.assertNotIn(self.students[-1].email, [e.to[0] for e in mail.outbox])

    def test_send_to_all(self):
        """
        Make sure email send to all goes there.
        """

        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        # the 1 is for the instructor
        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

    @override_settings(BULK_EMAIL_JOB_SIZE_THRESHOLD=1)
    def test_send_to_all_high_queue(self):
        """
        Test that email is still sent when the high priority queue is used
        """
        self.test_send_to_all()

    def test_no_duplicate_emails_staff_instructor(self):
        """
        Test that no duplicate emails are sent to a course instructor that is
        also course staff
        """
        CourseStaffRole(self.course.id).add_users(self.instructor)
        self.test_send_to_all()

    def test_no_duplicate_emails_enrolled_staff(self):
        """
        Test that no duplicate emails are sent to a course instructor that is
        also enrolled in the course
        """
        CourseEnrollment.enroll(self.instructor, self.course.id)
        self.test_send_to_all()

    def test_no_duplicate_emails_unenrolled_staff(self):
        """
        Test that no duplicate emails are sent to a course staff that is
        not enrolled in the course, but is enrolled in other courses
        """
        course_1 = CourseFactory.create()
        course_2 = CourseFactory.create()
        # make sure self.instructor isn't enrolled in the course
        self.assertFalse(CourseEnrollment.is_enrolled(self.instructor, self.course.id))
        CourseEnrollment.enroll(self.instructor, course_1.id)
        CourseEnrollment.enroll(self.instructor, course_2.id)
        self.test_send_to_all()

    def test_unicode_subject_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """

        uni_subject = u'téśt śúbjéćt főŕ áĺĺ'
        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': uni_subject,
            'message': 'test message for all'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )
        self.assertEquals(mail.outbox[0].subject, uni_subject)

    def test_unicode_students_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """

        # Create a student with Unicode in their first & last names
        unicode_user = UserFactory(first_name=u'Ⓡⓞⓑⓞⓣ', last_name=u'ՇﻉรՇ')
        CourseEnrollmentFactory.create(user=unicode_user, course_id=self.course.id)
        self.students.append(unicode_user)

        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))

        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

    @override_settings(BULK_EMAIL_DEFAULT_FROM_EMAIL="no-reply@courseupdates.edx.org")
    def test_long_course_display_name(self):
        """
        This test tests that courses with exorbitantly large display names
        can still send emails, since it appears that 320 appears to be the
        character length limit of from emails for Amazon SES.
        """
        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': 'test subject for self',
            'message': 'test message for self'
        }

        # make display_name that's longer than 320 characters when encoded
        # to ascii and escaped, but shorter than 320 unicode characters
        long_name = u"Финансовое программирование и политика, часть 1: макроэкономические счета и анализ"

        course = CourseFactory.create(
            display_name=long_name,
            org="IMF",
            number="FPP.1x",
            run="2016",
        )
        instructor = InstructorFactory(course_key=course.id)

        unexpected_from_addr = _get_source_address(
            course.id, course.display_name, truncate=False
        )
        __, encoded_unexpected_from_addr = forbid_multi_line_headers(
            "from", unexpected_from_addr, 'utf-8'
        )
        escaped_encoded_unexpected_from_addr = escape(encoded_unexpected_from_addr)

        # it's shorter than 320 characters when just encoded
        self.assertEqual(len(encoded_unexpected_from_addr), 318)
        # escaping it brings it over that limit
        self.assertEqual(len(escaped_encoded_unexpected_from_addr), 324)
        # when not escaped or encoded, it's well below 320 characters
        self.assertEqual(len(unexpected_from_addr), 137)

        self.login_as_user(instructor)
        send_mail_url = reverse('send_email', kwargs={'course_id': unicode(course.id)})
        response = self.client.post(send_mail_url, test_email)
        self.assertTrue(json.loads(response.content)['success'])

        self.assertEqual(len(mail.outbox), 1)
        from_email = mail.outbox[0].from_email

        expected_from_addr = (
            u'"{course_name}" Course Staff <{course_name}-no-reply@courseupdates.edx.org>'
        ).format(course_name=course.id.course)

        self.assertEqual(
            from_email,
            expected_from_addr
        )
        self.assertEqual(len(from_email), 61)

    @override_settings(BULK_EMAIL_EMAILS_PER_TASK=3)
    @patch('bulk_email.tasks.update_subtask_status')
    def test_chunked_queries_send_numerous_emails(self, email_mock):
        """
        Test sending a large number of emails, to test the chunked querying
        """
        mock_factory = MockCourseEmailResult()
        email_mock.side_effect = mock_factory.get_mock_update_subtask_status()
        added_users = []
        for _ in xrange(LARGE_NUM_EMAILS):
            user = UserFactory()
            added_users.append(user)
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        optouts = []
        for i in [1, 3, 9, 10, 18]:  # 5 random optouts
            user = added_users[i]
            optouts.append(user)
            optout = Optout(user=user, course_id=self.course.id)
            optout.save()

        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(mock_factory.emails_sent,
                          1 + len(self.staff) + len(self.students) + LARGE_NUM_EMAILS - len(optouts))
        outbox_contents = [e.to[0] for e in mail.outbox]
        should_send_contents = ([self.instructor.email] +
                                [s.email for s in self.staff] +
                                [s.email for s in self.students] +
                                [s.email for s in added_users if s not in optouts])
        self.assertItemsEqual(outbox_contents, should_send_contents)


@attr('shard_1')
@skipIf(os.environ.get("TRAVIS") == 'true', "Skip this test in Travis CI.")
class TestEmailSendFromDashboard(EmailSendFromDashboardTestCase):
    """
    Tests email sending without mocked html_to_text.

    Note that these tests are skipped on Travis because we can't use the
    function `html_to_text` as it is currently implemented on Travis.
    """

    def test_unicode_message_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """

        uni_message = u'ẗëṡẗ ṁëṡṡäġë ḟöṛ äḷḷ ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ fоѓ аll'
        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': 'test subject for all',
            'message': uni_message
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

        message_body = mail.outbox[0].body
        self.assertIn(uni_message, message_body)


@ddt.ddt
class TestCourseEmailContext(SharedModuleStoreTestCase):
    """
    Test the course email context hash used to send bulk emails.
    """

    @classmethod
    def setUpClass(cls):
        """
        Create a course, InstructorTask, and CourseEmail shared by all tests.
        """
        super(TestCourseEmailContext, cls).setUpClass()
        cls.course_title = u"Финансовое программирование и политика, часть 1: макроэкономические счета и анализ"
        cls.course_org = 'IMF'
        cls.course_number = "FPP.1x"
        cls.course_run = "2016"
        cls.course = CourseFactory.create(
            display_name=cls.course_title,
            org=cls.course_org,
            number=cls.course_number,
            run=cls.course_run,
        )
        cls.user = UserFactory()
        cls.course_email = CourseEmail.create(
            course_id=cls.course.id,
            sender=cls.user,
            targets=[SEND_TO_MYSELF],
            subject='subject',
            html_message='message',
        )
        cls.email_task = InstructorTask.create(
            course_id=cls.course.id,
            task_type='bulk_course_email',
            task_key='key',
            task_input={},
            requester=cls.user,
        )

    @ddt.data(
        (False, 'http'),
        (True, 'https'),
    )
    @ddt.unpack
    def test_context_urls(self, is_secure, scheme):
        """
        This test tests that the bulk email context uses http or https urls as appropriate.
        """
        email_context = _get_course_email_context(self.course, is_secure)
        self.assertEquals(email_context['platform_name'], 'edX')
        self.assertEquals(email_context['course_title'], self.course_title)
        self.assertEquals(email_context['course_url'],
                          '{}://edx.org/courses/{}/{}/{}/'.format(scheme,
                                                                  self.course_org,
                                                                  self.course_number,
                                                                  self.course_run))
        self.assertEquals(email_context['course_image_url'],
                          '{}://edx.org/c4x/{}/{}/asset/images_course_image.jpg'.format(scheme,
                                                                                        self.course_org,
                                                                                        self.course_number))
        self.assertEquals(email_context['email_settings_url'], '{}://edx.org/dashboard'.format(scheme))
        self.assertEquals(email_context['account_settings_url'], '{}://edx.org/account/settings'.format(scheme))

    @ddt.data(
        None,
        False,
        True,
    )
    @patch('bulk_email.tasks._get_course_email_context')
    def test_task_input_is_secure(self, is_secure, get_course_email_context):
        """
        Test the effect of different task_input hashes on perform_delegate_email_batches,
        to ensure that the correct http or https URL schemes are used in generated emails.
        """
        task_input = {'email_id': self.course_email.id}
        if is_secure is not None:
            task_input['is_secure'] = is_secure
        else:
            # https URLs used by default to maintain backwards compatibility
            is_secure = True

        perform_delegate_email_batches(self.email_task.id, self.course.id, task_input, 'emailed')
        get_course_email_context.assert_called_with(self.course, is_secure)
