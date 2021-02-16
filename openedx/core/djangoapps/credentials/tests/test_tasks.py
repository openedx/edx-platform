"""
Test credentials tasks
"""

import pytest
import mock
from django.conf import settings
from django.test import TestCase, override_settings

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory

from openedx.core.djangoapps.credentials.tasks.v1 import tasks

TASKS_MODULE = 'openedx.core.djangoapps.credentials.tasks.v1.tasks'


def boom():
    raise Exception('boom')


@skip_unless_lms
@mock.patch(TASKS_MODULE + '.get_credentials_api_client')
@override_settings(CREDENTIALS_SERVICE_USERNAME='test-service-username')
class TestSendGradeToCredentialTask(TestCase):
    """
    Tests for the 'send_grade_to_credentials' method.
    """
    def setUp(self):
        super(TestSendGradeToCredentialTask, self).setUp()  # lint-amnesty, pylint: disable=super-with-arguments
        self.user = UserFactory.create(username=settings.CREDENTIALS_SERVICE_USERNAME)

    def test_happy_path(self, mock_get_api_client):
        """
        Test that we actually do check expiration on each entitlement (happy path)
        """
        api_client = mock.MagicMock()
        mock_get_api_client.return_value = api_client

        tasks.send_grade_to_credentials.delay('user', 'course-v1:org+course+run', True, 'A', 1.0).get()

        assert mock_get_api_client.call_count == 1
        assert mock_get_api_client.call_args[0] == (self.user,)
        self.assertDictEqual(mock_get_api_client.call_args[1], {'org': 'org'})

        assert api_client.grades.post.call_count == 1
        self.assertDictEqual(api_client.grades.post.call_args[0][0], {
            'username': 'user',
            'course_run': 'course-v1:org+course+run',
            'letter_grade': 'A',
            'percent_grade': 1.0,
            'verified': True,
        })

    def test_retry(self, mock_get_api_client):
        """
        Test that we retry when an exception occurs.
        """
        mock_get_api_client.side_effect = boom

        task = tasks.send_grade_to_credentials.delay('user', 'course-v1:org+course+run', True, 'A', 1.0)

        pytest.raises(Exception, task.get)
        assert mock_get_api_client.call_count == (tasks.MAX_RETRIES + 1)
