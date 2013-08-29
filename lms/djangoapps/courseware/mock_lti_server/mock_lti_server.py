from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import json
import urllib
import urlparse
import threading

from logging import getLogger
logger = getLogger(__name__)


# todo - implement oauth

class MockLTIRequestHandler(BaseHTTPRequestHandler):
    '''
    A handler for LTI POST requests.
    '''

    protocol = "HTTP/1.0"

    def do_HEAD(self):
        self._send_head()

    def do_POST(self):
        '''
        Handle a POST request from the client and sends response back.
        '''
        self._send_head()

        post_dict = self._post_dict()  # Retrieve the POST data

        # Log the request
        logger.debug("LTI provider received POST request {} to path {}".format(
            str(post_dict),
            self.path)
        )
        # Respond only to requests with correct lti endpoint:
        if self._is_correct_lti_request():
            correct_dict = {
                'user_id': 'default_user_id',
                'oauth_nonce': '22990037033121997701377766132',
                'oauth_timestamp': '1377766132',
                'oauth_consumer_key': 'client_key',
                'lti_version': 'LTI-1p0',
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_version': '1.0',
                'oauth_signature': 'HGYMAU/G5EMxd0CDOvWubsqxLIY=',
                'lti_message_type': 'basic-lti-launch-request',
                'oauth_callback': 'about:blank'
            }

            if sorted(correct_dict.keys()) != sorted(post_dict.keys()):
                error_message = "Incorrect LTI header"
            else:
                error_message = "This is LTI tool."
        else:
            error_message = "Invalid request URL"

        self._send_response(error_message)

    def _send_head(self):
        '''
        Send the response code and MIME headers
        '''
        if self._is_correct_lti_request():
            self.send_response(200)
        else:
            self.send_response(500)

        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _post_dict(self):
        '''
        Retrieve the POST parameters from the client as a dictionary
        '''
        try:
            length = int(self.headers.getheader('content-length'))
            post_dict = urlparse.parse_qs(self.rfile.read(length))
            # The POST dict will contain a list of values for each key.
            # None of our parameters are lists, however, so we map [val] --> val.
            #I f the list contains multiple entries, we pick the first one
            post_dict = dict(
                map(
                    lambda (key, list_val): (key, list_val[0]),
                    post_dict.items()
                )
            )
        except:
            # We return an empty dict here, on the assumption
            # that when we later check that the request has
            # the correct fields, it won't find them,
            # and will therefore send an error response
            return {}
        return post_dict

    def _send_response(self, message):
        '''
        Send message back to the client
        '''
        response_str = """<html><head><title>TEST TITLE</title></head>
        <body>
        <div><h2>IFrame loaded</h2> \
        <h3>Server response is:</h3>\
        <h3 class="result">{}</h3></div>
        </body></html>""".format(message)

        # Log the response
        logger.debug("LTI: sent response {}".format(response_str))

        self.wfile.write(response_str)

    def _is_correct_lti_request(self):
        '''If url to get LTI is correct.'''
        return 'correct_lti_endpoint' in self.path


class MockLTIServer(HTTPServer):
    '''
    A mock LTI provider server that responds
    to POST requests to localhost.
    '''

    def __init__(self, port_num, oauth={}):
        '''
        Initialize the mock XQueue server instance.

        *port_num* is the localhost port to listen to

        *grade_response_dict* is a dictionary that will be JSON-serialized
            and sent in response to XQueue grading requests.
        '''

        self.clent_key = oauth.get('client_key', '')
        self.clent_secret = oauth.get('client_secret', '')
        self.check_oauth()

        handler = MockLTIRequestHandler
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

    def get_oauth_signature(self):
        '''test'''
        return self._signature

    def check_oauth(self):
        ''' generate oauth signature '''
        self._signature = '12345'

