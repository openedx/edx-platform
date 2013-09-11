from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urlparse
import mock
import threading
import json
from logging import getLogger
logger = getLogger(__name__)
import time

class MockYoutubeRequestHandler(BaseHTTPRequestHandler):
    '''
    A handler for Youtube GET requests.
    '''

    protocol = "HTTP/1.0"

    def do_HEAD(self):
        self._send_head()

    def do_GET(self):
        '''
        Handle a GET request from the client and sends response back.
        '''
        self._send_head()

        logger.debug("Youtube provider received GET request to path {}".format(
            self.path)
        )  # Log the request

        status_message = "I'm youtube."
        response_timeout = float(self.server.time_to_response)

        # threading timer produces TypeError: 'NoneType' object is not callable here
        # so we use time.sleep, as we already in separate thread.
        time.sleep(response_timeout)
        self._send_response(status_message)

    def _send_head(self):
        '''
        Send the response code and MIME headers
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _send_response(self, message):
        '''
        Send message back to the client
        '''
        callback = urlparse.parse_qs(self.path)['callback'][0]
        response = callback + '({})'.format(json.dumps({'message': message}))
        # Log the response
        logger.debug("Youtube: sent response {}".format(message))

        self.wfile.write(response)


class MockYoutubeServer(HTTPServer):
    '''
    A mock Youtube provider server that responds
    to GET requests to localhost.
    '''

    def __init__(self, address):
        '''
        Initialize the mock XQueue server instance.

        *address* is the (host, host's port to listen to) tuple.
        '''
        handler = MockYoutubeRequestHandler
        HTTPServer.__init__(self, address, handler)

    def shutdown(self):
        '''
        Stop the server and free up the port
        '''
        # First call superclass shutdown()
        HTTPServer.shutdown(self)
        # We also need to manually close the socket
        self.socket.close()
