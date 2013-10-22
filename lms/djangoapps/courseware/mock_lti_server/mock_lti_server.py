from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urlparse
from oauthlib.oauth1.rfc5849 import signature
import mock
import sys
from logging import getLogger
logger = getLogger(__name__)


class MockLTIRequestHandler(BaseHTTPRequestHandler):
    '''
    A handler for LTI POST requests.
    '''

    protocol = "HTTP/1.0"

    def log_message(self, format, *args):
        """Log an arbitrary message."""
        # Code copied from BaseHTTPServer.py. Changed to write to sys.stdout
        # so that messages won't pollute test output.
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format % args))

    def do_HEAD(self):
        self._send_head()

    def do_POST(self):
        '''
        Handle a POST request from the client and sends response back.
        '''
        self._send_head()

        post_dict = self._post_dict()  # Retrieve the POST data

        logger.debug("LTI provider received POST request {} to path {}".format(
            str(post_dict),
            self.path)
        )  # Log the request

        # Respond only to requests with correct lti endpoint:
        if self._is_correct_lti_request():
            correct_keys = [
                'user_id',
                'role',
                'oauth_nonce',
                'oauth_timestamp',
                'oauth_consumer_key',
                'lti_version',
                'oauth_signature_method',
                'oauth_version',
                'oauth_signature',
                'lti_message_type',
                'oauth_callback',
                'lis_outcome_service_url',
                'lis_result_sourcedid',
                'launch_presentation_return_url'
            ]

            if sorted(correct_keys) != sorted(post_dict.keys()):
                status_message = "Incorrect LTI header"
            else:
                params = {k: v for k, v in post_dict.items() if k != 'oauth_signature'}
                if self.server.check_oauth_signature(params, post_dict['oauth_signature']):
                    status_message = "This is LTI tool. Success."
                else:
                    status_message = "Wrong LTI signature"
        else:
            status_message = "Invalid request URL"

        self._send_response(status_message)

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
            post_dict = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=True)
            # The POST dict will contain a list of values for each key.
            # None of our parameters are lists, however, so we map [val] --> val.
            # If the list contains multiple entries, we pick the first one
            post_dict = {key: val[0] for key, val in post_dict.items()}
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
        '''If url to LTI tool is correct.'''
        return self.server.oauth_settings['lti_endpoint'] in self.path


class MockLTIServer(HTTPServer):
    '''
    A mock LTI provider server that responds
    to POST requests to localhost.
    '''

    def __init__(self, address):
        '''
        Initialize the mock XQueue server instance.

        *address* is the (host, host's port to listen to) tuple.
        '''
        handler = MockLTIRequestHandler
        HTTPServer.__init__(self, address, handler)

    def shutdown(self):
        '''
        Stop the server and free up the port
        '''
        # First call superclass shutdown()
        HTTPServer.shutdown(self)
        # We also need to manually close the socket
        self.socket.close()

    def check_oauth_signature(self, params, client_signature):
        '''
        Checks oauth signature from client.

        `params` are params from post request except signature,
        `client_signature` is signature from request.

        Builds mocked request and verifies hmac-sha1 signing::
            1. builds string to sign from `params`, `url` and `http_method`.
            2. signs it with `client_secret` which comes from server settings.
            3. obtains signature after sign and then compares it with request.signature
            (request signature comes form client in request)

        Returns `True` if signatures are correct, otherwise `False`.

        '''
        client_secret = unicode(self.oauth_settings['client_secret'])
        url = self.oauth_settings['lti_base'] + self.oauth_settings['lti_endpoint']

        request = mock.Mock()

        request.params = [(unicode(k), unicode(v)) for k, v in params.items()]
        request.uri = unicode(url)
        request.http_method = u'POST'
        request.signature = unicode(client_signature)

        return signature.verify_hmac_sha1(request, client_secret)

