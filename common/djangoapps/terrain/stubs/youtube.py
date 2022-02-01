"""
Stub implementation of YouTube for acceptance tests.


To start this stub server on its own from Vagrant:

1.) Locally, modify your Vagrantfile so that it contains:

    config.vm.network :forwarded_port, guest: 8031, host: 8031

2.) From within Vagrant dev environment do:

    cd common/djangoapps/terrain
    python -m stubs.start youtube 8031

3.) Locally, try accessing http://localhost:8031/ and see that
    you get "Unused url" message inside the browser.
"""


import json
import time
from collections import OrderedDict

import requests
from six.moves.urllib.parse import urlparse

from .http import StubHttpRequestHandler, StubHttpService


class StubYouTubeHandler(StubHttpRequestHandler):
    """
    A handler for Youtube GET requests.
    """

    # Default number of seconds to delay the response to simulate network latency.
    DEFAULT_DELAY_SEC = 0.5

    def do_DELETE(self):  # pylint: disable=invalid-name
        """
        Allow callers to delete all the server configurations using the /del_config URL.
        """
        if self.path in ("/del_config", "/del_config/"):
            self.server.config = {}
            self.log_message("Reset Server Configuration.")
            self.send_response(200)
        else:
            self.send_response(404)

    def do_GET(self):
        """
        Handle a GET request from the client and sends response back.
        """
        self.log_message(
            f"Youtube provider received GET request to path {self.path}"
        )

        if 'get_config' in self.path:
            self.send_json_response(self.server.config)

        elif 'test_transcripts_youtube' in self.path:

            if 't__eq_exist' in self.path:
                status_message = "".join([
                    '<?xml version="1.0" encoding="utf-8" ?>',
                    '<transcript><text start="1.0" dur="1.0">',
                    'Equal transcripts</text></transcript>'
                ]).encode('utf-8')

                self.send_response(
                    200, content=status_message, headers={'Content-type': 'application/xml'}
                )

            elif 't_neq_exist' in self.path:
                status_message = "".join([
                    '<?xml version="1.0" encoding="utf-8" ?>',
                    '<transcript><text start="1.1" dur="5.5">',
                    'Transcripts sample, different that on server',
                    '</text></transcript>'
                ]).encode('utf-8')

                self.send_response(
                    200, content=status_message, headers={'Content-type': 'application/xml'}
                )

            else:
                self.send_response(404)

        elif 'test_youtube' in self.path:
            params = urlparse(self.path)
            youtube_id = params.path.split('/').pop()

            if self.server.config.get('youtube_api_private_video'):
                self._send_private_video_response(youtube_id, "I'm youtube private video.")  # lint-amnesty, pylint: disable=too-many-function-args
            else:
                self._send_video_response(youtube_id, "I'm youtube.")

        elif 'get_youtube_api' in self.path:
            # Delay the response to simulate network latency
            time.sleep(self.server.config.get('time_to_response', self.DEFAULT_DELAY_SEC))
            if self.server.config.get('youtube_api_blocked'):
                self.send_response(404, content=b'', headers={'Content-type': 'text/plain'})
            else:
                # Get the response to send from YouTube.
                # We need to do this every time because Google sometimes sends different responses
                # as part of their own experiments, which has caused our tests to become "flaky"
                self.log_message("Getting iframe api from youtube.com")
                iframe_api_response = requests.get('https://www.youtube.com/iframe_api').content.strip(b"\n")
                self.send_response(200, content=iframe_api_response, headers={'Content-type': 'text/html'})

        else:
            self.send_response(
                404, content=b"Unused url", headers={'Content-type': 'text/plain'}
            )

    def _send_video_response(self, youtube_id, message):
        """
        Send message back to the client for video player requests.
        Requires sending back callback id.
        """
        # Delay the response to simulate network latency
        time.sleep(self.server.config.get('time_to_response', self.DEFAULT_DELAY_SEC))

        # Construct the response content
        callback = self.get_params['callback']

        data = OrderedDict({
            'items': list(
                OrderedDict({
                    'contentDetails': OrderedDict({
                        'id': youtube_id,
                        'duration': 'PT2M20S',
                    })
                })
            )
        })
        response = f"{callback}({json.dumps(data)})".encode('utf-8')

        self.send_response(200, content=response, headers={'Content-type': 'text/html'})
        self.log_message(f"Youtube: sent response {message}")

    def _send_private_video_response(self, message):
        """
        Send private video error message back to the client for video player requests.
        """
        # Construct the response content
        callback = self.get_params['callback']
        data = OrderedDict({
            "error": OrderedDict({
                "code": 403,
                "errors": [
                    {
                        "code": "ServiceForbiddenException",
                        "domain": "GData",
                        "internalReason": "Private video"
                    }
                ],
                "message": message,
            })
        })
        response = f"{callback}({json.dumps(data)})".encode('utf-8')

        self.send_response(200, content=response, headers={'Content-type': 'text/html'})
        self.log_message(f"Youtube: sent response {message}")


class StubYouTubeService(StubHttpService):
    """
    A stub Youtube provider server that responds to GET requests to localhost.
    """

    HANDLER_CLASS = StubYouTubeHandler
