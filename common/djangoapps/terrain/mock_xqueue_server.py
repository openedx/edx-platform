from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import json
import urllib
import urlparse


class MockXQueueRequestHandler(BaseHTTPRequestHandler):
    '''
    A handler for XQueue POST requests.
    '''

    protocol = "HTTP/1.0"

    def do_HEAD(self):
        self._send_head()

    def do_POST(self):
        '''
        Handle a POST request from the client, interpreted
        as either a login request or a submission for grading request.

        Sends back an immediate success/failure response.
        If grading is required, it then POSTS back to the client
        with grading results, as configured in MockXQueueServer.
        '''
        self._send_head()

        # Retrieve the POST data
        post_dict = self._post_dict()

        # Send a response indicating success/failure
        success = self._send_immediate_response(post_dict)

        # If the client submitted a valid submission request,
        # we need to post back to the callback url
        # with the grading result
        if success and self._is_grade_request():
            self._send_grade_response(post_dict['lms_callback_url'],
                                        post_dict['lms_key'])

    def _send_head(self):
        '''
        Send the response code and MIME headers
        '''
        if self._is_login_request() or self._is_grade_request():
            self.send_response(200)
        else:
            self.send_response(500)

        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def _post_dict(self):
        '''
        Retrieve the POST parameters from the client as a dictionary
        '''

        try:
            length = int(self.headers.getheader('content-length'))

            post_dict = urlparse.parse_qs(self.rfile.read(length))

            # The POST dict will contain a list of values
            # for each key.
            # None of our parameters are lists, however,
            # so we map [val] --> val
            # If the list contains multiple entries,
            # we pick the first one
            post_dict = dict(map(lambda (key, list_val): (key, list_val[0]),
                                post_dict.items()))

        except:
            # We return an empty dict here, on the assumption
            # that when we later check that the request has
            # the correct fields, it won't find them,
            # and will therefore send an error response
            return {}

        return post_dict

    def _send_immediate_response(self, post_dict):
        '''
        Check the post_dict for the appropriate fields
        for this request (login or grade submission)
        If it finds them, inform the client of success.
        Otherwise, inform the client of failure
        '''

        # Allow any user to log in, as long as the POST
        # dict has a username and password
        if self._is_login_request():
            success = 'username' in post_dict and 'password' in post_dict

        elif self._is_grade_request():
            success = ('lms_callback_url' in post_dict and
                        'lms_key' in post_dict and
                        'queue_name' in post_dict)
        else:
            success = False

        # Send the response indicating success/failure
        response_str = json.dumps({'return_code': 0 if success else 1,
                                'content': '' if success else 'Error'})

        self.wfile.write(response_str)

        return success

    def _send_grade_response(self, postback_url, queuekey):
        '''
        POST the grade response back to the client
        using the response provided by the server configuration
        '''
        response_dict = {'queuekey': queuekey,
                        'xqueue_body': self.server.grade_response}

        MockXQueueRequestHandler.post_to_url(postback_url, response_dict)

    def _is_login_request(self):
        return 'xqueue/login' in self.path

    def _is_grade_request(self):
        return 'xqueue/submit' in self.path

    @staticmethod
    def post_to_url(url, param_dict):
        '''
        POST *param_dict* to *url*
        We make this a separate function so we can easily patch
        it during testing.
        '''
        urllib.urlopen(url, urllib.urlencode(param_dict))


class MockXQueueServer(HTTPServer):
    '''
    A mock XQueue grading server that responds
    to POST requests to localhost.
    '''

    def __init__(self, port_num, grade_response_dict):
        '''
        Initialize the mock XQueue server instance.

        *port_num* is the localhost port to listen to

        *grade_response_dict* is a dictionary that will be JSON-serialized
            and sent in response to XQueue grading requests.
        '''

        self.grade_response = grade_response_dict

        handler = MockXQueueRequestHandler
        address = ('', port_num)
        HTTPServer.__init__(self, address, handler)

    @property
    def grade_response(self):
        return self._grade_response

    @grade_response.setter
    def grade_response(self, grade_response_dict):
        self._grade_response = grade_response_dict


# ----------------------------
# Tests

import mock
import threading
import unittest


class MockXQueueServerTest(unittest.TestCase):

    def setUp(self):

        # Create the server
        server_port = 8034
        self.server_url = 'http://127.0.0.1:%d' % server_port
        self.server = MockXQueueServer(server_port,
                                {'correct': True, 'score': 1, 'msg': ''})

        # Start the server in a separate daemon thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def tearDown(self):

        # Stop the server, freeing up the port
        self.server.shutdown()
        self.server.socket.close()

    def test_login_request(self):

        # Send a login request
        login_request = {'username': 'Test', 'password': 'Test'}
        response_handle = urllib.urlopen(self.server_url + '/xqueue/login',
                                urllib.urlencode(login_request))
        response_dict = json.loads(response_handle.read())
        self.assertEqual(response_dict['return_code'], 0)

    def test_grade_request(self):

        # Patch post_to_url() so we can intercept
        # outgoing POST requests from the server
        MockXQueueRequestHandler.post_to_url = mock.Mock()

        # Send a grade request
        callback_url = 'http://127.0.0.1:8000/test_callback'
        grade_request = {'lms_callback_url': callback_url,
                        'lms_key': 'test_queuekey',
                        'queue_name': 'test_queue'}
        response_handle = urllib.urlopen(self.server_url + '/xqueue/submit',
                                urllib.urlencode(grade_request))
        response_dict = json.loads(response_handle.read())

        # Expect that the response is success
        self.assertEqual(response_dict['return_code'], 0)

        # Expect that the server tries to post back the grading info
        expected_callback_dict = {'queuekey': 'test_queuekey',
                                'xqueue_body': {'correct': True,
                                                'score': 1, 'msg': ''}}
        MockXQueueRequestHandler.post_to_url.assert_called_with(callback_url,
                                                        expected_callback_dict)
