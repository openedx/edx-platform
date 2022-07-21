"""
LMS Interface to external queueing system (xqueue)
"""

import hashlib
import json
import logging

import requests
import six

log = logging.getLogger(__name__)
dateformat = '%Y%m%d%H%M%S'

XQUEUE_METRIC_NAME = 'edxapp.xqueue'

# Wait time for response from Xqueue.
XQUEUE_TIMEOUT = 35  # seconds
CONNECT_TIMEOUT = 3.05  # seconds
READ_TIMEOUT = 10  # seconds


def make_hashkey(seed):
    """
    Generate a string key by hashing
    """
    h = hashlib.md5()
    h.update(six.b(str(seed)))
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


class XQueueInterface(object):
    """
    Interface to the external grading system
    """

    def __init__(self, url, django_auth, requests_auth=None):
        self.url = six.text_type(url)
        self.auth = django_auth
        self.session = requests.Session()
        self.session.auth = requests_auth

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
        construct_callback(callable): function which constructs a fully-qualified callback URL to make xqueue requests.
        default_queuename(string): course-specific queue name.
        waittime(int): number of seconds to wait between xqueue requests
        url(string): base URL for the XQueue service.
        django_auth(dict): username and password for the XQueue service.
        basic_auth(array or None): basic authentication credentials, if needed.
    """
    def __init__(self, construct_callback, default_queuename, waittime, url, django_auth, basic_auth=None):

        requests_auth = requests.auth.HTTPBasicAuth(*basic_auth) if basic_auth else None
        self._interface = XQueueInterface(url, django_auth, requests_auth)

        self._construct_callback = construct_callback
        self._default_queuename = default_queuename.replace(' ', '_')
        self._waittime = waittime

    @property
    def interface(self):
        """
        Returns the XQueueInterface instance.
        """
        return self._interface

    @property
    def construct_callback(self):
        """
        Returns the function to construct the XQueue callback.
        """
        return self._construct_callback

    @property
    def default_queuename(self):
        """
        Returns the default queue name for the current course.
        """
        return self._default_queuename

    @property
    def waittime(self):
        """
        Returns the number of seconds to wait in between calls to XQueue.
        """
        return self._waittime
