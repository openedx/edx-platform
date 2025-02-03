"""Test the XQueue service and interface."""

from unittest import TestCase
from unittest.mock import Mock, patch

from django.conf import settings
from django.test.utils import override_settings
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.fields import ScopeIds
from waffle.testutils import override_switch
import json

from openedx.core.djangolib.testing.utils import skip_unless_lms
from xmodule.capa.xqueue_interface import XQueueInterface, XQueueService
import pytest


@skip_unless_lms
class XQueueServiceTest(TestCase):
    """Test the XQueue service methods."""
    def setUp(self):
        super().setUp()
        location = BlockUsageLocator(CourseLocator("test_org", "test_course", "test_run"), "problem", "ExampleProblem")
        self.block = Mock(scope_ids=ScopeIds('user1', 'mock_problem', location, location))
        self.service = XQueueService(self.block)

    def test_interface(self):
        """Test that the `XQUEUE_INTERFACE` settings are passed from the service to the interface."""
        assert isinstance(self.service.interface, XQueueInterface)
        assert self.service.interface.url == 'http://sandbox-xqueue.edx.org'
        assert self.service.interface.auth['username'] == 'lms'
        assert self.service.interface.auth['password'] == '***REMOVED***'
        assert self.service.interface.session.auth.username == 'anant'
        assert self.service.interface.session.auth.password == 'agarwal'

    def test_construct_callback(self):
        """Test that the XQueue callback is initialized correctly, and can be altered through the settings."""
        usage_id = self.block.scope_ids.usage_id
        callback_url = f'courses/{usage_id.context_key}/xqueue/user1/{usage_id}'

        assert self.service.construct_callback() == f'{settings.LMS_ROOT_URL}/{callback_url}/score_update'
        assert self.service.construct_callback('alt_dispatch') == f'{settings.LMS_ROOT_URL}/{callback_url}/alt_dispatch'

        custom_callback_url = 'http://alt.url'
        with override_settings(XQUEUE_INTERFACE={**settings.XQUEUE_INTERFACE, 'callback_url': custom_callback_url}):
            assert self.service.construct_callback() == f'{custom_callback_url}/{callback_url}/score_update'

    def test_default_queuename(self):
        """Check the format of the default queue name."""
        assert self.service.default_queuename == 'test_org-test_course'

    def test_waittime(self):
        """Check that the time between requests is retrieved correctly from the settings."""
        assert self.service.waittime == 5

        with override_settings(XQUEUE_WAITTIME_BETWEEN_REQUESTS=15):
            assert self.service.waittime == 15


@pytest.mark.django_db
@override_switch('xqueue_submission.enabled', active=True)
@patch('xmodule.capa.xqueue_submission.XQueueInterfaceSubmission.send_to_submission')
def test_send_to_queue_with_waffle_enabled(mock_send_to_submission):
    """Prueba que el flujo de trabajo de edx-submissions se utiliza cuando el switch de waffle está habilitado."""
    url = "http://example.com/xqueue"
    django_auth = {"username": "user", "password": "pass"}
    requests_auth = None
    xqueue_interface = XQueueInterface(url, django_auth, requests_auth)

    header = json.dumps({
        'lms_callback_url': 'http://example.com/courses/course-v1:test_org+test_course+test_run/xqueue/block@item_id/type@problem',
    })
    body = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer'
    })
    files_to_upload = None

    mock_send_to_submission.return_value = {'submission': 'mock_submission'}
    error, msg = xqueue_interface.send_to_queue(header, body, files_to_upload)
    
    assert error == 0
    assert msg == "Submission sent successfully"
    mock_send_to_submission.assert_called_once_with(header, body, {})


@pytest.mark.django_db
@override_switch('xqueue_submission.enabled', active=False)
@patch('xmodule.capa.xqueue_interface.XQueueInterface._http_post')
def test_send_to_queue_with_waffle_disabled(mock_http_post):
    """Prueba que el flujo de trabajo de XQueue se utiliza cuando el switch de waffle está deshabilitado."""
    url = "http://example.com/xqueue"
    django_auth = {"username": "user", "password": "pass"}
    requests_auth = None
    xqueue_interface = XQueueInterface(url, django_auth, requests_auth)

    header = json.dumps({
        'lms_callback_url': 'http://example.com/courses/course-v1:test_org+test_course+test_run/xqueue/block@item_id/type@problem',
    })
    body = json.dumps({
        'student_info': json.dumps({'anonymous_student_id': 'student_id'}),
        'student_response': 'student_answer'
    })
    files_to_upload = None

    mock_http_post.return_value = (0, "Submission sent successfully")
    error, msg = xqueue_interface.send_to_queue(header, body, files_to_upload)
    
    assert error == 0
    assert msg == "Submission sent successfully"
    mock_http_post.assert_called_once_with(
        'http://example.com/xqueue/xqueue/submit/',
        {'xqueue_header': header, 'xqueue_body': body},
        files={}
    )