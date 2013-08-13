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
        code = 200
        if 'test_transcripts_youtube' in self.path:
            if not 'trans_exist' in self.path:
                code = 404
        self._send_head(code)

    def do_GET(self):
        '''
        Handle a GET request from the client and sends response back.
        '''
        logger.debug("Youtube provider received GET request to path {}".format(
            self.path)
        )  # Log the request

        if 'test_transcripts_youtube' in self.path:
            if 't__eq_exist' in self.path:
                status_message = """<?xml version="1.0" encoding="utf-8" ?><transcript><text start="1.0" dur="1.0">Equal transcripts</text></transcript>"""
                self._send_head()
                self._send_transcripts_response(status_message)
            elif 't_neq_exist' in self.path:
                status_message = """<?xml version="1.0" encoding="utf-8" ?><transcript><text start="1.1" dur="5.5">Transcripts sample, different that on server</text></transcript>"""
                self._send_head()
                self._send_transcripts_response(status_message)
            else:
                self._send_head(404)
        elif 'test_youtube' in self.path:
            self._send_head()
            #testing videoplayers
            status_message = "I'm youtube."
            response_timeout = float(self.server.time_to_response)

            # threading timer produces TypeError: 'NoneType' object is not callable here
            # so we use time.sleep, as we already in separate thread.
            time.sleep(response_timeout)
            self._send_video_response(status_message)
        else:
            # unused url
            self._send_head()
            self._send_transcripts_response('Unused url')
            logger.debug("Request to unused url.")

    def _send_head(self, code=200):
        '''
        Send the response code and MIME headers
        '''

        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _send_transcripts_response(self, message):
        '''
        Send message back to the client for transcripts ajax requests.
        '''
        response = message
        # Log the response
        logger.debug("Youtube: sent response {}".format(message))

        self.wfile.write(response)

    def _send_video_response(self, message):
        '''
        Send message back to the client for video player requests.
        Requires sending back callback id.
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
