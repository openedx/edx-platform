import json
import mock

from django.http import HttpResponse
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from rest_framework import status


class SupportEmailTestCase(TestCase):
    """
    Tests email sending via contact/support form.
    """

    @classmethod
    def setUpClass(cls):
        super(SupportEmailTestCase, cls).setUpClass()
        cls.client = Client()
        cls.send_mail_url = reverse('ucsd_support_email')
        cls.test_email = {
            'subject': 'Subject goes here',
            'comment': {'body': 'here goes the body/details'},
            'tags': ['LMS'],
            'requester': {
                'email': 'edx@example.com',
                'name': 'edx'
            },
            'custom_fields': [{
                'value': 'course-v1:edX+DemoX+Demo_Course'
            }]
        }

    def test_send_email_successful(self):
        """
        Make sure email works successfully.
        """
        response = self.client.post(self.send_mail_url,
                                    data=json.dumps(self.test_email),
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch(
        'django.test.Client.post', return_value=HttpResponse(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ), autospec=True
    )
    def test_send_email_fail(self, mock_func):
        """
        Make sure email fails successfully.
        """

        response = self.client.post(self.send_mail_url,
                                    data=json.dumps(self.test_email),
                                    content_type='application/json')

        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
