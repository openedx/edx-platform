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
from .http import StubHttpRequestHandler, StubHttpService
import json
import time
import requests
from urlparse import urlparse
from collections import OrderedDict


IFRAME_API_RESPONSE = requests.get('https://www.youtube.com/iframe_api').content.strip("\n")


class StubYouTubeHandler(StubHttpRequestHandler):
    """
    A handler for Youtube GET requests.
    """

    # Default number of seconds to delay the response to simulate network latency.
    DEFAULT_DELAY_SEC = 0.5

    def do_DELETE(self):  # pylint: disable=C0103
        """
        Allow callers to delete all the server configurations using the /del_config URL.
        """
        if self.path == "/del_config" or self.path == "/del_config/":
            self.server.config = dict()
            self.log_message("Reset Server Configuration.")
            self.send_response(200)
        else:
            self.send_response(404)

    def do_GET(self):
        """
        Handle a GET request from the client and sends response back.
        """

        self.log_message(
            "Youtube provider received GET request to path {}".format(self.path)
        )

        if 'get_config' in self.path:
            self.send_json_response(self.server.config)

        elif 'test_transcripts_youtube' in self.path:

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

        elif 'get_youtube_api' in self.path:
            if self.server.config.get('youtube_api_blocked'):
                self.send_response(404, content='', headers={'Content-type': 'text/plain'})
            else:
                self.send_response(200, content=IFRAME_API_RESPONSE, headers={'Content-type': 'text/html'})

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
        time.sleep(self.server.config.get('time_to_response', self.DEFAULT_DELAY_SEC))

        # Construct the response content
        callback = self.get_params['callback']
        youtube_metadata = json.loads(
            requests.get(
                "http://gdata.youtube.com/feeds/api/videos/{id}?v=2&alt=jsonc".format(id=youtube_id)
            ).text
        )
        data = OrderedDict({
            'data': OrderedDict({
                'id': youtube_id,
                'message': message,
                'duration': youtube_metadata['data']['duration'],
            })
        })
        response = "{cb}({data})".format(cb=callback, data=json.dumps(data))

        self.send_response(200, content=response, headers={'Content-type': 'text/html'})
        self.log_message("Youtube: sent response {}".format(message))


class StubYouTubeService(StubHttpService):
    """
    A stub Youtube provider server that responds to GET requests to localhost.
    """

    HANDLER_CLASS = StubYouTubeHandler
