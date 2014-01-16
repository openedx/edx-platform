"""
Fixture to configure XQueue response.
"""

import requests
import json
from bok_choy.web_app_fixture import WebAppFixture, WebAppFixtureError
from . import XQUEUE_STUB_URL


class XQueueResponseFixture(WebAppFixture):
    """
    Configure the XQueue stub's response to submissions.
    """

    def __init__(self, queue_name, response_dict):
        """
        Configure XQueue stub to POST `response_dict` (a dictionary)
        back to the LMS when it receives a submission to a queue
        named `queue_name`.

        Remember that there is one XQueue stub shared by all the tests;
        if possible, you should have tests use unique queue names
        to avoid conflict between tests running in parallel.
        """
        self._queue_name = queue_name
        self._response_dict = response_dict

    def install(self):
        """
        Configure the stub via HTTP.
        """
        url = XQUEUE_STUB_URL + "/set_config"

        # Configure the stub to respond to submissions to our queue
        payload = {self._queue_name: json.dumps(self._response_dict)}
        response = requests.put(url, data=payload)

        if not response.ok:
            raise WebFixtureError(
                "Could not configure XQueue stub for queue '{1}'.  Status code: {2}".format(
                    self._queue_name, self._response_dict))
