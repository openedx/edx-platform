"""
Stub implementation of YouTube for acceptance tests.
"""

from .http import StubHttpRequestHandler, StubHttpService
import json
import time
import requests
from urlparse import urlparse
from collections import OrderedDict


class StubYouTubeHandler(StubHttpRequestHandler):
    """
    A handler for Youtube GET requests.
    """

    # Default number of seconds to delay the response to simulate network latency.
    DEFAULT_DELAY_SEC = 0.5

    def do_GET(self):
        """
        Handle a GET request from the client and sends response back.
        """

        self.log_message(
            "Youtube provider received GET request to path {}".format(self.path)
        )

        if 'test_transcripts_youtube' in self.path:

            if 't__eq_exist' in self.path:
                status_message = "".join([
                    '<?xml version="1.0" encoding="utf-8" ?>',
                    '<transcript><text start="1.0" dur="1.0">',
                    'Equal transcripts</text></transcript>'
                ])

                self.send_response(
                    200, content=status_message, headers={'Content-type': 'application/xml'}
                )

            elif 't_neq_exist' in self.path:
                status_message = "".join([
                    '<?xml version="1.0" encoding="utf-8" ?>',
                    '<transcript><text start="1.1" dur="5.5">',
                    'Transcripts sample, different that on server',
                    '</text></transcript>'
                ])

                self.send_response(
                    200, content=status_message, headers={'Content-type': 'application/xml'}
                )

            else:
                self.send_response(404)

        elif 'test_youtube' in self.path:
            params = urlparse(self.path)
            youtube_id = params.path.split('/').pop()

            self._send_video_response(youtube_id, "I'm youtube.")
            # self._send_video_response("I'm youtube.")

        else:
            self.send_response(
                404, content="Unused url", headers={'Content-type': 'text/plain'}
            )

    def _send_video_response(self, youtube_id, message):
        """
        Send message back to the client for video player requests.
        Requires sending back callback id.
        """
        # Delay the response to simulate network latency
        time.sleep(self.server.config('time_to_response', self.DEFAULT_DELAY_SEC))

        # Construct the response content
        callback = self.get_params['callback'][0]
        data = OrderedDict({
            'data': OrderedDict({
                'id': youtube_id,
                'message': message,
                'duration': 60,
            })
        })
        # import ipdb; ipdb.set_trace()
        response = callback + '({})'.format(json.dumps(data))

        # response = callback + '({})'.format(json.dumps({'message': message}))

        self.send_response(200, content=response, headers={'Content-type': 'text/html'})
        self.log_message("Youtube: sent response {}".format(message))


class StubYouTubeService(StubHttpService):
    """
    A stub Youtube provider server that responds to GET requests to localhost.
    """

    HANDLER_CLASS = StubYouTubeHandler
