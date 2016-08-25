# -*- coding: utf-8 -*-
"""
Unit tests for the localization of emails sent by instructor.api methods.
"""

from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from nose.plugins.attrib import attr

from courseware.tests.factories import InstructorFactory
from lang_pref import LANGUAGE_KEY
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference, delete_user_preference
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


@attr(shard=1)
class TestInstructorAPIEnrollmentEmailLocalization(SharedModuleStoreTestCase):
    """
    Test whether the enroll, unenroll and beta role emails are sent in the
    proper language, i.e: the student's language.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorAPIEnrollmentEmailLocalization, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestInstructorAPIEnrollmentEmailLocalization, self).setUp()

        # Platform language is English, instructor's language is Chinese,
        # student's language is French, so the emails should all be sent in
        # French.
        self.instructor = InstructorFactory(course_key=self.course.id)
        set_user_preference(self.instructor, LANGUAGE_KEY, 'zh-cn')
        self.client.login(username=self.instructor.username, password='test')

        self.student = UserFactory.create()
        set_user_preference(self.student, LANGUAGE_KEY, 'fr')

    def update_enrollement(self, action, student_email):
        """
        Update the current student enrollment status.
        """
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        args = {'identifiers': student_email, 'email_students': 'true', 'action': action, 'reason': 'testing'}
        response = self.client.post(url, args)
        return response

    def check_outbox_is_french(self):
        """
        Check that the email outbox contains exactly one message for which both
        the message subject and body contain a certain French string.
        """
        return self.check_outbox(u"Vous avez été")

    def check_outbox(self, expected_message):
        """
        Check that the email outbox contains exactly one message for which both
        the message subject and body contain a certain string.
        """
        self.assertEqual(1, len(mail.outbox))
        self.assertIn(expected_message, mail.outbox[0].subject)
        self.assertIn(expected_message, mail.outbox[0].body)

    def test_enroll(self):
        self.update_enrollement("enroll", self.student.email)

        self.check_outbox_is_french()

    def test_unenroll(self):
        CourseEnrollment.enroll(
            self.student,
            self.course.id
        )
        self.update_enrollement("unenroll", self.student.email)

        self.check_outbox_is_french()

    def test_set_beta_role(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.client.post(url, {'identifiers': self.student.email, 'action': 'add', 'email_students': 'true'})

        self.check_outbox_is_french()

    def test_enroll_unsubscribed_student(self):
        # Student is unknown, so the platform language should be used
        self.update_enrollement("enroll", "newuser@hotmail.com")
        self.check_outbox("You have been")

    @override_settings(LANGUAGE_CODE="fr")
    def test_user_without_preference_receives_email_in_french(self):
        delete_user_preference(self.student, LANGUAGE_KEY)
        self.update_enrollement("enroll", self.student.email)

        self.check_outbox_is_french()
