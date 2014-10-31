"""
Tools for creating edxnotes content fixture data.
"""

from datetime import datetime

import factory
import requests

from . import EDXNOTES_STUB_URL


class Note(factory.Factory):
    id = None
    annotator_schema_version = "v1.0"
    created = datetime.utcnow().isoformat()
    updated = datetime.utcnow().isoformat()
    user = "dummy-user-id"
    username = "dummy-username"
    course_id = "dummy-course-id"
    text = "dummy note text"
    quote = "dummy note quote"
    ranges = [
        {
            "start": "/p[1]",
            "end": "/p[1]",
            "startOffset": 0,
            "endOffset": 10
        }
    ]


class EdxNotesFixture(object):

    def push(self):
        """
        Push the data to the stub comments service.
        """
        requests.put(
            '{}/set_config'.format(EDXNOTES_STUB_URL),
            data=self.get_config_data()
        )

    def get_config_data(self):
        """
        return a dictionary with the fixture's data serialized for PUTting to the stub server's config endpoint.
        """
        raise NotImplementedError()
