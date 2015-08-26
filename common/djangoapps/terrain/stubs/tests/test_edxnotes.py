"""
Unit tests for stub EdxNotes implementation.
"""

import json
import unittest
import requests
from uuid import uuid4
from ..edxnotes import StubEdxNotesService


class StubEdxNotesServiceTest(unittest.TestCase):
    """
    Test cases for the stub EdxNotes service.
    """
    def setUp(self):
        """
        Start the stub server.
        """
        super(StubEdxNotesServiceTest, self).setUp()
        self.server = StubEdxNotesService()
        dummy_notes = self._get_dummy_notes(count=2)
        self.server.add_notes(dummy_notes)
        self.addCleanup(self.server.shutdown)

    def _get_dummy_notes(self, count=1):
        """
        Returns a list of dummy notes.
        """
        return [self._get_dummy_note() for i in xrange(count)]  # pylint: disable=unused-variable

    def _get_dummy_note(self):
        """
        Returns a single dummy note.
        """
        nid = uuid4().hex
        return {
            "id": nid,
            "created": "2014-10-31T10:05:00.000000",
            "updated": "2014-10-31T10:50:00.101010",
            "user": "dummy-user-id",
            "usage_id": "dummy-usage-id",
            "course_id": "dummy-course-id",
            "text": "dummy note text " + nid,
            "quote": "dummy note quote",
            "ranges": [
                {
                    "start": "/p[1]",
                    "end": "/p[1]",
                    "startOffset": 0,
                    "endOffset": 10,
                }
            ],
        }

    def test_note_create(self):
        dummy_note = {
            "user": "dummy-user-id",
            "usage_id": "dummy-usage-id",
            "course_id": "dummy-course-id",
            "text": "dummy note text",
            "quote": "dummy note quote",
            "ranges": [
                {
                    "start": "/p[1]",
                    "end": "/p[1]",
                    "startOffset": 0,
                    "endOffset": 10,
                }
            ],
        }
        response = requests.post(self._get_url("api/v1/annotations"), data=json.dumps(dummy_note))
        self.assertTrue(response.ok)
        response_content = response.json()
        self.assertIn("id", response_content)
        self.assertIn("created", response_content)
        self.assertIn("updated", response_content)
        self.assertIn("annotator_schema_version", response_content)
        self.assertDictContainsSubset(dummy_note, response_content)

    def test_note_read(self):
        notes = self._get_notes()
        for note in notes:
            response = requests.get(self._get_url("api/v1/annotations/" + note["id"]))
            self.assertTrue(response.ok)
            self.assertDictEqual(note, response.json())

        response = requests.get(self._get_url("api/v1/annotations/does_not_exist"))
        self.assertEqual(response.status_code, 404)

    def test_note_update(self):
        notes = self._get_notes()
        for note in notes:
            response = requests.get(self._get_url("api/v1/annotations/" + note["id"]))
            self.assertTrue(response.ok)
            self.assertDictEqual(note, response.json())

        response = requests.get(self._get_url("api/v1/annotations/does_not_exist"))
        self.assertEqual(response.status_code, 404)

    def test_search(self):
        response = requests.get(self._get_url("api/v1/search"), params={
            "user": "dummy-user-id",
            "usage_id": "dummy-usage-id",
            "course_id": "dummy-course-id",
        })
        notes = self._get_notes()
        self.assertTrue(response.ok)
        self.assertDictEqual({"total": 2, "rows": notes}, response.json())

        response = requests.get(self._get_url("api/v1/search"))
        self.assertEqual(response.status_code, 400)

    def test_delete(self):
        notes = self._get_notes()
        response = requests.delete(self._get_url("api/v1/annotations/does_not_exist"))
        self.assertEqual(response.status_code, 404)

        for note in notes:
            response = requests.delete(self._get_url("api/v1/annotations/" + note["id"]))
            self.assertEqual(response.status_code, 204)
            remaining_notes = self.server.get_notes()
            self.assertNotIn(note["id"], [note["id"] for note in remaining_notes])

        self.assertEqual(len(remaining_notes), 0)

    def test_update(self):
        note = self._get_notes()[0]
        response = requests.put(self._get_url("api/v1/annotations/" + note["id"]), data=json.dumps({
            "text": "new test text"
        }))
        self.assertEqual(response.status_code, 200)

        updated_note = self._get_notes()[0]
        self.assertEqual("new test text", updated_note["text"])
        self.assertEqual(note["id"], updated_note["id"])
        self.assertItemsEqual(note, updated_note)

        response = requests.get(self._get_url("api/v1/annotations/does_not_exist"))
        self.assertEqual(response.status_code, 404)

    def test_notes_collection(self):
        response = requests.get(self._get_url("api/v1/annotations"), params={"user": "dummy-user-id"})
        self.assertTrue(response.ok)
        self.assertEqual(len(response.json()), 2)

        response = requests.get(self._get_url("api/v1/annotations"))
        self.assertEqual(response.status_code, 400)

    def test_cleanup(self):
        response = requests.put(self._get_url("cleanup"))
        self.assertTrue(response.ok)
        self.assertEqual(len(self.server.get_notes()), 0)

    def test_create_notes(self):
        dummy_notes = self._get_dummy_notes(count=2)
        response = requests.post(self._get_url("create_notes"), data=json.dumps(dummy_notes))
        self.assertTrue(response.ok)
        self.assertEqual(len(self._get_notes()), 4)

        response = requests.post(self._get_url("create_notes"))
        self.assertEqual(response.status_code, 400)

    def test_headers(self):
        note = self._get_notes()[0]
        response = requests.get(self._get_url("api/v1/annotations/" + note["id"]))
        self.assertTrue(response.ok)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "*")

        response = requests.options(self._get_url("api/v1/annotations/"))
        self.assertTrue(response.ok)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "*")
        self.assertEqual(response.headers.get("access-control-allow-methods"), "GET, POST, PUT, DELETE, OPTIONS")
        self.assertIn("X-CSRFToken", response.headers.get("access-control-allow-headers"))

    def _get_notes(self):
        """
        Return a list of notes from the stub EdxNotes service.
        """
        notes = self.server.get_notes()
        self.assertGreater(len(notes), 0, "Notes are empty.")
        return notes

    def _get_url(self, path):
        """
        Construt a URL to the stub EdxNotes service.
        """
        return "http://127.0.0.1:{port}/{path}/".format(
            port=self.server.port, path=path
        )
