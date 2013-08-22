# -*- coding: utf-8 -*-
"""
Unit tests for sending course email
"""

from django.test.utils import override_settings
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import UserFactory, GroupFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from bulk_email.tasks import delegate_email_batches, course_email
from bulk_email.models import CourseEmail

from mock import patch

STAFF_COUNT = 3
STUDENT_COUNT = 10


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestEmailSendFromDashboard(ModuleStoreTestCase):
    """
    Test that emails send correctly.
    """

    @patch.dict(settings.MITX_FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True})
    def setUp(self):
        self.course = CourseFactory.create()
        self.instructor = UserFactory.create(username="instructor", email="robot+instructor@edx.org")
        # Create instructor group for course
        instructor_group = GroupFactory.create(name="instructor_MITx/999/Robot_Super_Course")
        instructor_group.user_set.add(self.instructor)

        # Create staff
        self.staff = [UserFactory() for _ in xrange(STAFF_COUNT)]
        staff_group = GroupFactory()
        for staff in self.staff:
            staff_group.user_set.add(staff)  # pylint: disable=E1101

        # Create students
        self.students = [UserFactory() for _ in xrange(STUDENT_COUNT)]
        for student in self.students:
            CourseEnrollmentFactory.create(user=student, course_id=self.course.id)

        self.client.login(username=self.instructor.username, password="test")

        # Pull up email view on instructor dashboard
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        response = self.client.get(self.url)
        email_link = '<a href="#" onclick="goto(\'Email\')" class="None">Email</a>'
        # If this fails, it is likely because ENABLE_INSTRUCTOR_EMAIL is set to False
        self.assertTrue(email_link in response.content)

        # Select the Email view of the instructor dash
        session = self.client.session
        session['idash_mode'] = 'Email'
        session.save()
        response = self.client.get(self.url)
        selected_email_link = '<a href="#" onclick="goto(\'Email\')" class="selectedmode">Email</a>'
        self.assertTrue(selected_email_link in response.content)

    def tearDown(self):
        """
        Undo all patches.
        """
        patch.stopall()

    def test_send_to_self(self):
        """
        Make sure email send to myself goes to myself.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.
        test_email = {
            'action': 'Send email',
            'to_option': 'myself',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEquals(mail.outbox[0].to[0], self.instructor.email)
        self.assertEquals(
            mail.outbox[0].subject,
            '[' + self.course.display_name + ']' + ' test subject for myself'
        )

    def test_send_to_staff(self):
        """
        Make sure email send to staff and instructors goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.
        test_email = {
            'action': 'Send email',
            'to_option': 'staff',
            'subject': 'test subject for staff',
            'message': 'test message for subject'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1 + len(self.staff))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff]
        )

    def test_send_to_all(self):
        """
        Make sure email send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

    def test_unicode_subject_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': u'téśt śúbjéćt főŕ áĺĺ',
            'message': 'test message for all'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )
        self.assertEquals(
            mail.outbox[0].subject,
            '[' + self.course.display_name + ']' + u' téśt śúbjéćt főŕ áĺĺ'
        )

    def test_unicode_message_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': u'ẗëṡẗ ṁëṡṡäġë ḟöṛ äḷḷ ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ fоѓ аll'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

        self.assertIn(
            u'ẗëṡẗ ṁëṡṡäġë ḟöṛ äḷḷ ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ fоѓ аll',
            mail.outbox[0].body
        )

    def test_unicode_students_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        # Create a student with Unicode in their first & last names
        unicode_user = UserFactory(first_name=u'Ⓡⓞⓑⓞⓣ', last_name=u'ՇﻉรՇ')
        CourseEnrollmentFactory.create(user=unicode_user, course_id=self.course.id)
        self.students.append(unicode_user)

        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))

        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestEmailSendExceptions(ModuleStoreTestCase):
    """
    Test that exceptions are handled correctly.
    """

    def test_get_course_exc(self):
        # Make sure delegate_email_batches handles Http404 exception from get_course_by_id.
        with self.assertRaises(Exception):
            delegate_email_batches("_", "_", "blah/blah/blah", "_", "_")

    def test_no_course_email_obj(self):
        # Make sure course_email handles CourseEmail.DoesNotExist exception.
        with self.assertRaises(CourseEmail.DoesNotExist):
            course_email("dummy hash", [], "_", "_", False)
