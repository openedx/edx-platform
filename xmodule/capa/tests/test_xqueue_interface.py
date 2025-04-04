"""Test the XQueue service and interface."""

from unittest import TestCase
from unittest.mock import Mock, patch

from django.conf import settings
from django.test.utils import override_settings
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.fields import ScopeIds
import pytest
import json

from openedx.core.djangolib.testing.utils import skip_unless_lms
from xmodule.capa.xqueue_interface import XQueueInterface, XQueueService


@pytest.mark.django_db
@skip_unless_lms
class XQueueServiceTest(TestCase):
    """Test the XQueue service methods."""

    def setUp(self):
        super().setUp()
        location = BlockUsageLocator(
            CourseLocator("test_org", "test_course", "test_run"),
            "problem",
            "ExampleProblem",
        )
        self.block = Mock(scope_ids=ScopeIds("user1", "mock_problem", location, location))
        self.block.max_score = Mock(return_value=10)  # Mock max_score method
        self.service = XQueueService(self.block)

    def test_interface(self):
        """Test that the `XQUEUE_INTERFACE` settings are passed from the service to the interface."""
        assert isinstance(self.service.interface, XQueueInterface)
        assert self.service.interface.url == "http://sandbox-xqueue.edx.org"
        assert self.service.interface.auth["username"] == "lms"
        assert self.service.interface.auth["password"] == "***REMOVED***"
        assert self.service.interface.session.auth.username == "anant"
        assert self.service.interface.session.auth.password == "agarwal"

    @patch("xmodule.capa.xqueue_interface.use_edx_submissions_for_xqueue", return_value=True)
    def test_construct_callback_with_flag_enabled(self, mock_flag):
        """Test construct_callback when the waffle flag is enabled."""
        usage_id = self.block.scope_ids.usage_id
        course_id = str(usage_id.course_key)
        callback_url = f"courses/{course_id}/xqueue/user1/{usage_id}"

        assert self.service.construct_callback() == f"{settings.LMS_ROOT_URL}/{callback_url}/score_update"
        assert self.service.construct_callback("alt_dispatch") == (
            f"{settings.LMS_ROOT_URL}/{callback_url}/alt_dispatch"
        )

        custom_callback_url = "http://alt.url"
        with override_settings(XQUEUE_INTERFACE={**settings.XQUEUE_INTERFACE, "callback_url": custom_callback_url}):
            assert self.service.construct_callback() == f"{custom_callback_url}/{callback_url}/score_update"

    @patch("xmodule.capa.xqueue_interface.use_edx_submissions_for_xqueue", return_value=False)
    def test_construct_callback_with_flag_disabled(self, mock_flag):
        """Test construct_callback when the waffle flag is disabled."""
        usage_id = self.block.scope_ids.usage_id
        callback_url = f'courses/{usage_id.context_key}/xqueue/user1/{usage_id}'

        assert self.service.construct_callback() == f'{settings.LMS_ROOT_URL}/{callback_url}/score_update'
        assert self.service.construct_callback('alt_dispatch') == f'{settings.LMS_ROOT_URL}/{callback_url}/alt_dispatch'

        custom_callback_url = 'http://alt.url'
        with override_settings(XQUEUE_INTERFACE={**settings.XQUEUE_INTERFACE, 'callback_url': custom_callback_url}):
            assert self.service.construct_callback() == f'{custom_callback_url}/{callback_url}/score_update'

    def test_default_queuename(self):
        """Check the format of the default queue name."""
        assert self.service.default_queuename == "test_org-test_course"

    def test_waittime(self):
        """Check that the time between requests is retrieved correctly from the settings."""
        assert self.service.waittime == 5

        with override_settings(XQUEUE_WAITTIME_BETWEEN_REQUESTS=15):
            assert self.service.waittime == 15


@pytest.mark.django_db
@patch("xmodule.capa.xqueue_interface.use_edx_submissions_for_xqueue", return_value=True)
@patch("xmodule.capa.xqueue_submission.XQueueInterfaceSubmission.send_to_submission")
def test_send_to_queue_with_flag_enabled(mock_send_to_submission, mock_flag):
    """Test send_to_queue when the waffle flag is enabled."""
    url = "http://example.com/xqueue"
    django_auth = {"username": "user", "password": "pass"}
    block = Mock()  # Mock block for the constructor
    xqueue_interface = XQueueInterface(url, django_auth, block=block)

    header = json.dumps({
        "lms_callback_url": (
            "http://example.com/courses/course-v1:test_org+test_course+test_run/"
            "xqueue/block@item_id/type@problem"
        ),
    })
    body = json.dumps({
        "student_info": json.dumps({"anonymous_student_id": "student_id"}),
        "student_response": "student_answer",
    })
    files_to_upload = None

    mock_send_to_submission.return_value = {"submission": "mock_submission"}
    error, msg = xqueue_interface.send_to_queue(header, body, files_to_upload)

    mock_send_to_submission.assert_called_once_with(header, body, {})


@pytest.mark.django_db
@patch("xmodule.capa.xqueue_interface.use_edx_submissions_for_xqueue", return_value=False)
@patch("xmodule.capa.xqueue_interface.XQueueInterface._http_post")
def test_send_to_queue_with_flag_disabled(mock_http_post, mock_flag):
    """Test send_to_queue when the waffle flag is disabled."""
    url = "http://example.com/xqueue"
    django_auth = {"username": "user", "password": "pass"}
    block = Mock()  # Mock block for the constructor
    xqueue_interface = XQueueInterface(url, django_auth, block=block)

    header = json.dumps({
        "lms_callback_url": (
            "http://example.com/courses/course-v1:test_org+test_course+test_run/"
            "xqueue/block@item_id/type@problem"
        ),
    })
    body = json.dumps({
        "student_info": json.dumps({"anonymous_student_id": "student_id"}),
        "student_response": "student_answer",
    })
    files_to_upload = None

    mock_http_post.return_value = (0, "Submission sent successfully")
    error, msg = xqueue_interface.send_to_queue(header, body, files_to_upload)

    mock_http_post.assert_called_once_with(
        "http://example.com/xqueue/xqueue/submit/",
        {"xqueue_header": header, "xqueue_body": body},
        files={},
    )
