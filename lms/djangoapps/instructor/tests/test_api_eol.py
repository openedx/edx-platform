# -*- coding: utf-8 -*-
"""
Unit tests for instructor.api methods with eol customization (reply_to).
"""

from django.utils.translation import ugettext as _
from mock import Mock, patch
from six import text_type

from django.urls import reverse 

from bulk_email.models import BulkEmailFlag
from lms.djangoapps.courseware.models import StudentModule

from lms.djangoapps.courseware.tests.factories import (
    InstructorFactory
)

from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase

from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestInstructorSendEmail(SiteMixin, SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Checks that only instructors have access to email endpoints, and that
    these endpoints are only accessible with courses that actually exist,
    only with valid email messages.
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorSendEmail, cls).setUpClass()
        cls.course = CourseFactory.create()
        test_subject = u'\u1234 test subject'
        test_message = u'\u6824 test message'
        test_reply_to = 'dummy@email.dummy'
        cls.full_test_message = {
            'send_to': '["myself", "staff"]',
            'subject': test_subject,
            'message': test_message,
            'reply_to': test_reply_to # eol customization
        }
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)

    @classmethod
    def tearDownClass(cls):
        super(TestInstructorSendEmail, cls).tearDownClass()
        BulkEmailFlag.objects.all().delete()

    def setUp(self):
        super(TestInstructorSendEmail, self).setUp()

        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')

    def test_send_email_as_logged_in_instructor(self):
        url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.post(url, self.full_test_message) # test message with reply_to
        self.assertEqual(response.status_code, 200)