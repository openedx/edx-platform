"""
LMS Interface to external queueing system (xqueue)
"""
from typing import Dict, Optional, TYPE_CHECKING

import hashlib
import json
import logging

import requests
from django.conf import settings
from django.urls import reverse
from requests.auth import HTTPBasicAuth
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag
from opaque_keys.edx.keys import CourseKey
from xmodule.capa.xqueue_submission import XQueueInterfaceSubmission

if TYPE_CHECKING:
    from xmodule.capa_block import ProblemBlock

log = logging.getLogger(__name__)
dateformat = '%Y%m%d%H%M%S'

XQUEUE_METRIC_NAME = 'edxapp.xqueue'

# Wait time for response from Xqueue.
XQUEUE_TIMEOUT = 35  # seconds
CONNECT_TIMEOUT = 3.05  # seconds
READ_TIMEOUT = 10  # seconds

# .. toggle_name: send_to_submission_course.enable
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_description: Enables use of the submissions service instead of legacy xqueue for course problem submissions.
# .. toggle_default: False
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2024-04-03
# .. toggle_expiration_date: 2025-08-12
# .. toggle_will_remain_in_codebase: True
# .. toggle_tickets: none
# .. toggle_status: supported
SEND_TO_SUBMISSION_COURSE_FLAG = CourseWaffleFlag('send_to_submission_course.enable', __name__)


def use_edx_submissions_for_xqueue(course_key: CourseKey | None = None) -> bool:
    """
    Determines whether edx-submissions should be used instead of legacy XQueue.

    This helper abstracts the toggle logic so that the rest of the codebase is not tied
    to specific feature flag mechanics or rollout strategies.

    Args:
        course_key (CourseKey | None): Optional course key. If None, fallback to site-level toggle.

    Returns:
        bool: True if edx-submissions should be used, False otherwise.
    """
    return SEND_TO_SUBMISSION_COURSE_FLAG.is_enabled(course_key)


def make_hashkey(seed):
    """
    Generate a string key by hashing
    """
    h = hashlib.md5()
    h.update(str(seed).encode('latin-1'))
    return h.hexdigest()


def make_xheader(lms_callback_url, lms_key, queue_name):
    """
    Generate header for delivery and reply of queue request.

    Xqueue header is a JSON-serialized dict:
        { 'lms_callback_url': url to which xqueue will return the request (string),
          'lms_key': secret key used by LMS to protect its state (string),
          'queue_name': designate a specific queue within xqueue server, e.g. 'MITx-6.00x' (string)
        }
    """
    return json.dumps({
        'lms_callback_url': lms_callback_url,
        'lms_key': lms_key,
        'queue_name': queue_name
    })


def parse_xreply(xreply):
    """
    Parse the reply from xqueue. Messages are JSON-serialized dict:
        { 'return_code': 0 (success), 1 (fail)
          'content': Message from xqueue (string)
        }
    """
    try:
        xreply = json.loads(xreply)
    except ValueError as err:
        log.error(err)
        return (1, 'unexpected reply from server')

    return_code = xreply['return_code']
    content = xreply['content']

    return (return_code, content)


class XQueueInterface:
    """Initializes the XQueue interface."""

    def __init__(self, url: str, django_auth: Dict[str, str],
                 requests_auth: Optional[HTTPBasicAuth] = None,
                 block: 'ProblemBlock' = None):
        """
        Initializes the XQueue interface.

        Args:
            url (str): The URL of the XQueue service.
            django_auth (Dict[str, str]): Authentication credentials for Django.
            requests_auth (Optional[HTTPBasicAuth], optional): Authentication for HTTP requests. Defaults to None.
            block ('ProblemBlock', optional): Added as a parameter only to extract the course_id
                to check the course waffle flag `send_to_submission_course.enable`.
                This can be removed after the legacy xqueue is deprecated. Defaults to None.
        """
        self.url = url
        self.auth = django_auth
        self.session = requests.Session()
        self.session.auth = requests_auth
        self.block = block
        self.submission = XQueueInterfaceSubmission(self.block)

    def send_to_queue(self, header, body, files_to_upload=None):
        """
        Submit a request to xqueue.

        header: JSON-serialized dict in the format described in 'xqueue_interface.make_xheader'

        body: Serialized data for the receipient behind the queueing service. The operation of
                xqueue is agnostic to the contents of 'body'

        files_to_upload: List of file objects to be uploaded to xqueue along with queue request

        Returns (error_code, msg) where error_code != 0 indicates an error
        """

        # log the send to xqueue
        header_info = json.loads(header)
        queue_name = header_info.get('queue_name', '')  # lint-amnesty, pylint: disable=unused-variable

        # Attempt to send to queue
        (error, msg) = self._send_to_queue(header, body, files_to_upload)

        # Log in, then try again
        if error and (msg == 'login_required'):
            (error, content) = self._login()
            if error != 0:
                # when the login fails
                log.debug("Failed to login to queue: %s", content)
                return (error, content)
            if files_to_upload is not None:
                # Need to rewind file pointers
                for f in files_to_upload:
                    f.seek(0)
            (error, msg) = self._send_to_queue(header, body, files_to_upload)

        return error, msg

    def _login(self):  # lint-amnesty, pylint: disable=missing-function-docstring
        payload = {
            'username': self.auth['username'],
            'password': self.auth['password']
        }
        return self._http_post(self.url + '/xqueue/login/', payload)

    def _send_to_queue(self, header, body, files_to_upload):  # lint-amnesty, pylint: disable=missing-function-docstring
        payload = {
            'xqueue_header': header,
            'xqueue_body': body
        }
        files = {}
        if files_to_upload is not None:
            for f in files_to_upload:
                files.update({f.name: f})

        if self.block is None:
            # XQueueInterface: if self.block is None, falling back to legacy xqueue submission.
            log.error(
                "Unexpected None block: falling back to legacy xqueue submission. "
                "This may indicate a problem with the xqueue transition."
            )
            return self._http_post(self.url + '/xqueue/submit/', payload, files=files)

        course_key = self.block.scope_ids.usage_id.context_key

        if use_edx_submissions_for_xqueue(course_key):
            submission = self.submission.send_to_submission(header, body, files)
            return None, ''

        return self._http_post(self.url + '/xqueue/submit/', payload, files=files)

    def _http_post(self, url, data, files=None):  # lint-amnesty, pylint: disable=missing-function-docstring
        try:
            response = self.session.post(
                url, data=data, files=files, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
            )
        except requests.exceptions.ConnectionError as err:
            log.error(err)
            return 1, 'cannot connect to server'

        except requests.exceptions.ReadTimeout as err:
            log.error(err)
            return 1, 'failed to read from the server'

        if response.status_code not in [200]:
            return 1, 'unexpected HTTP status code [%d]' % response.status_code

        return parse_xreply(response.text)


class XQueueService:
    """
    XBlock service providing an interface to the XQueue service.

    Args:
        block: The `ProblemBlock` instance.
    """

    def __init__(self, block: 'ProblemBlock'):
        basic_auth = settings.XQUEUE_INTERFACE.get('basic_auth')
        requests_auth = HTTPBasicAuth(*basic_auth) if basic_auth else None
        self._interface = XQueueInterface(
            settings.XQUEUE_INTERFACE['url'], settings.XQUEUE_INTERFACE['django_auth'], requests_auth,
            block=block
        )

        self._block = block

    @property
    def interface(self):
        """
        Returns the XQueueInterface instance.
        """
        return self._interface

    def construct_callback(self, dispatch: str = "score_update") -> str:
        """
        Return a fully qualified callback URL for the external queueing system.
        """
        course_key = self._block.scope_ids.usage_id.context_key
        userid = str(self._block.scope_ids.user_id)
        mod_id = str(self._block.scope_ids.usage_id)

        callback_type = "xqueue_callback"

        relative_xqueue_callback_url = reverse(
            callback_type,
            kwargs={
                "course_id": str(course_key),
                "userid": userid,
                "mod_id": mod_id,
                "dispatch": dispatch,
            },
        )

        xqueue_callback_url_prefix = settings.XQUEUE_INTERFACE.get("callback_url", settings.LMS_ROOT_URL)
        return f"{xqueue_callback_url_prefix}{relative_xqueue_callback_url}"

    @property
    def default_queuename(self) -> str:
        """
        Returns the default queue name for the current course.
        """
        course_id = self._block.scope_ids.usage_id.context_key
        return f'{course_id.org}-{course_id.course}'.replace(' ', '_')

    @property
    def waittime(self) -> int:
        """
        Returns the number of seconds to wait in between calls to XQueue.
        """
        return settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS
