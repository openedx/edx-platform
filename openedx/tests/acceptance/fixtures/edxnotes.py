"""
Tools for creating edxnotes content fixture data.
"""

import json
import factory
import requests

from openedx.tests.acceptance.fixtures import EDXNOTES_STUB_URL


class Range(factory.Factory):
    class Meta(object):
        model = dict

    start = "/div[1]/p[1]"
    end = "/div[1]/p[1]"
    startOffset = 0
    endOffset = 8


class Note(factory.Factory):
    class Meta(object):
        model = dict

    user = "dummy-user"
    usage_id = "dummy-usage-id"
    course_id = "dummy-course-id"
    text = "dummy note text"
    quote = "dummy note quote"
    ranges = [Range()]


class EdxNotesFixtureError(Exception):
    """
    Error occurred while installing a edxnote fixture.
    """
    pass


class EdxNotesFixture(object):
    notes = []

    def create_notes(self, notes_list):
        self.notes = notes_list
        return self

    def install(self):
        """
        Push the data to the stub EdxNotes service.
        """
        response = requests.post(
            '{}/create_notes'.format(EDXNOTES_STUB_URL),
            data=json.dumps(self.notes)
        )

        if not response.ok:
            raise EdxNotesFixtureError(
                "Could not create notes {0}.  Status was {1}".format(
                    json.dumps(self.notes), response.status_code
                )
            )

        return self

    def cleanup(self):
        """
        Cleanup the stub EdxNotes service.
        """
        self.notes = []
        response = requests.put('{}/cleanup'.format(EDXNOTES_STUB_URL))

        if not response.ok:
            raise EdxNotesFixtureError(
                "Could not cleanup EdxNotes service {0}.  Status was {1}".format(
                    json.dumps(self.notes), response.status_code
                )
            )

        return self
