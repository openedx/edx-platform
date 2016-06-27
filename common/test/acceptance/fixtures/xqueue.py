"""
Fixture to configure XQueue response.
"""

import requests
import json

from common.test.acceptance.fixtures import XQUEUE_STUB_URL


class XQueueResponseFixtureError(Exception):
    """
    Error occurred while configuring the stub XQueue.
    """
    pass


class XQueueResponseFixture(object):
    """
    Configure the XQueue stub's response to submissions.
    """

    def __init__(self, pattern, response_dict):
        """
        Configure XQueue stub to POST `response_dict` (a dictionary)
        back to the LMS when it receives a submission that contains the string
        `pattern`.

        Remember that there is one XQueue stub shared by all the tests;
        if possible, you should have tests use unique queue names
        to avoid conflict between tests running in parallel.
        """
        self._pattern = pattern
        self._response_dict = response_dict

    def install(self):
        """
        Configure the stub via HTTP.
        """
        url = XQUEUE_STUB_URL + "/set_config"

        # Configure the stub to respond to submissions to our queue
        payload = {self._pattern: json.dumps(self._response_dict)}
        response = requests.put(url, data=payload)

        if not response.ok:
            raise XQueueResponseFixtureError(
                "Could not configure XQueue stub for queue '{1}'.  Status code: {2}".format(
                    self._pattern, self._response_dict))
