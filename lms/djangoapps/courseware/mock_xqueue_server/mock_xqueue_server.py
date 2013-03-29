from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import json
import urllib
import urlparse
import threading

from logging import getLogger
logger = getLogger(__name__)


class MockXQueueRequestHandler(BaseHTTPRequestHandler):
    '''
    A handler for XQueue POST requests.
    '''

    protocol = "HTTP/1.0"

    def do_HEAD(self):
        self._send_head()

    def do_POST(self):
        '''
        Handle a POST request from the client

        Sends back an immediate success/failure response.
        It then POSTS back to the client
        with grading results, as configured in MockXQueueServer.
        '''
        self._send_head()

        # Retrieve the POST data
        post_dict = self._post_dict()

        # Log the request
        logger.debug("XQueue received POST request %s to path %s" %
                    (str(post_dict), self.path))

        # Respond only to grading requests
        if self._is_grade_request():
            try:
                xqueue_header = json.loads(post_dict['xqueue_header'])
                xqueue_body = json.loads(post_dict['xqueue_body'])

                callback_url = xqueue_header['lms_callback_url']

            except KeyError:
                # If the message doesn't have a header or body,
                # then it's malformed.
                # Respond with failure
                error_msg = "XQueue received invalid grade request"
                self._send_immediate_response(False, message=error_msg)

            except ValueError:
                # If we could not decode the body or header,
                # respond with failure

                error_msg = "XQueue could not decode grade request"
                self._send_immediate_response(False, message=error_msg)

            else:
                # Send an immediate response of success
                # The grade request is formed correctly
                self._send_immediate_response(True)

                # Wait a bit before POSTing back to the callback url with the
                # grade result configured by the server
                # Otherwise, the problem will not realize it's
                # queued and it will keep waiting for a response
                # indefinitely
                delayed_grade_func = lambda: self._send_grade_response(callback_url,
                                                                        xqueue_header)

                timer = threading.Timer(2, delayed_grade_func)
                timer.start()

        # If we get a request that's not to the grading submission
        # URL, return an error
        else:
            error_message = "Invalid request URL"
            self._send_immediate_response(False, message=error_message)


    def _send_head(self):
        '''
        Send the response code and MIME headers
        '''
        if self._is_grade_request():
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

    def _send_immediate_response(self, success, message=""):
        '''
        Send an immediate success/failure message
        back to the client
        '''

        # Send the response indicating success/failure
        response_str = json.dumps({'return_code': 0 if success else 1,
                                'content': message})

        # Log the response
        logger.debug("XQueue: sent response %s" % response_str)

        self.wfile.write(response_str)

    def _send_grade_response(self, postback_url, xqueue_header):
        '''
        POST the grade response back to the client
        using the response provided by the server configuration
        '''
        response_dict = {'xqueue_header': json.dumps(xqueue_header),
                        'xqueue_body': json.dumps(self.server.grade_response())}

        # Log the response
        logger.debug("XQueue: sent grading response %s" % str(response_dict))

        MockXQueueRequestHandler.post_to_url(postback_url, response_dict)

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

    def __init__(self, port_num,
            grade_response_dict={'correct': True, 'score': 1, 'msg': ''}):
        '''
        Initialize the mock XQueue server instance.

        *port_num* is the localhost port to listen to

        *grade_response_dict* is a dictionary that will be JSON-serialized
            and sent in response to XQueue grading requests.
        '''

        self.set_grade_response(grade_response_dict)

        handler = MockXQueueRequestHandler
        address = ('', port_num)
        HTTPServer.__init__(self, address, handler)

    def shutdown(self):
        '''
        Stop the server and free up the port
        '''
        # First call superclass shutdown()
        HTTPServer.shutdown(self)

        # We also need to manually close the socket
        self.socket.close()

    def grade_response(self):
        return self._grade_response

    def set_grade_response(self, grade_response_dict):

        # Check that the grade response has the right keys
        assert('correct' in grade_response_dict and
                'score' in grade_response_dict and
                'msg' in grade_response_dict)

        # Wrap the message in <div> tags to ensure that it is valid XML
        grade_response_dict['msg'] = "<div>%s</div>" % grade_response_dict['msg']

        # Save the response dictionary
        self._grade_response = grade_response_dict
