"""
Unit tests for stub EdxNotes implementation.
"""
import urlparse
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
        dummy_notes = self._get_dummy_notes(count=5)
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
        # Without user
        response = requests.get(self._get_url("api/v1/search"))
        self.assertEqual(response.status_code, 400)

        # get response with default page and page size
        response = requests.get(self._get_url("api/v1/search"), params={
            "user": "dummy-user-id",
            "usage_id": "dummy-usage-id",
            "course_id": "dummy-course-id",
        })

        self.assertTrue(response.ok)
        self._verify_pagination_info(
            response=response.json(),
            total_notes=5,
            num_pages=3,
            notes_per_page=2,
            start=0,
            current_page=1,
            next_page=2,
            previous_page=None
        )

        # search notes with text that don't exist
        response = requests.get(self._get_url("api/v1/search"), params={
            "user": "dummy-user-id",
            "usage_id": "dummy-usage-id",
            "course_id": "dummy-course-id",
            "text": "world war 2"
        })

        self.assertTrue(response.ok)
        self._verify_pagination_info(
            response=response.json(),
            total_notes=0,
            num_pages=0,
            notes_per_page=0,
            start=0,
            current_page=1,
            next_page=None,
            previous_page=None
        )

    def test_delete(self):
        notes = self._get_notes()
        response = requests.delete(self._get_url("api/v1/annotations/does_not_exist"))
        self.assertEqual(response.status_code, 404)

        for note in notes:
            response = requests.delete(self._get_url("api/v1/annotations/" + note["id"]))
            self.assertEqual(response.status_code, 204)
            remaining_notes = self.server.get_all_notes()
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

    # pylint: disable=too-many-arguments
    def _verify_pagination_info(
            self,
            response,
            total_notes,
            num_pages,
            notes_per_page,
            current_page,
            previous_page,
            next_page,
            start
    ):
        """
        Verify the pagination information.

        Argument:
            response: response from api
            total_notes: total notes in the response
            num_pages: total number of pages in response
            notes_per_page: number of notes in the response
            current_page: current page number
            previous_page: previous page number
            next_page: next page number
            start: start of the current page
        """
        def get_page_value(url):
            """
            Return page value extracted from url.
            """
            if url is None:
                return None

            parsed = urlparse.urlparse(url)
            query_params = urlparse.parse_qs(parsed.query)

            page = query_params["page"][0]
            return page if page is None else int(page)

        self.assertEqual(response["total"], total_notes)
        self.assertEqual(response["num_pages"], num_pages)
        self.assertEqual(len(response["rows"]), notes_per_page)
        self.assertEqual(response["current_page"], current_page)
        self.assertEqual(get_page_value(response["previous"]), previous_page)
        self.assertEqual(get_page_value(response["next"]), next_page)
        self.assertEqual(response["start"], start)

    def test_notes_collection(self):
        """
        Test paginated response of notes api
        """

        # Without user
        response = requests.get(self._get_url("api/v1/annotations"))
        self.assertEqual(response.status_code, 400)

        # Without any pagination parameters
        response = requests.get(self._get_url("api/v1/annotations"), params={"user": "dummy-user-id"})

        self.assertTrue(response.ok)
        self._verify_pagination_info(
            response=response.json(),
            total_notes=5,
            num_pages=3,
            notes_per_page=2,
            start=0,
            current_page=1,
            next_page=2,
            previous_page=None
        )

        # With pagination parameters
        response = requests.get(self._get_url("api/v1/annotations"), params={
            "user": "dummy-user-id",
            "page": 2,
            "page_size": 3
        })

        self.assertTrue(response.ok)
        self._verify_pagination_info(
            response=response.json(),
            total_notes=5,
            num_pages=2,
            notes_per_page=2,
            start=3,
            current_page=2,
            next_page=None,
            previous_page=1
        )

    def test_notes_collection_next_previous_with_one_page(self):
        """
        Test next and previous urls of paginated response of notes api
        when number of pages are 1
        """
        response = requests.get(self._get_url("api/v1/annotations"), params={
            "user": "dummy-user-id",
            "page_size": 10
        })

        self.assertTrue(response.ok)
        self._verify_pagination_info(
            response=response.json(),
            total_notes=5,
            num_pages=1,
            notes_per_page=5,
            start=0,
            current_page=1,
            next_page=None,
            previous_page=None
        )

    def test_notes_collection_when_no_notes(self):
        """
        Test paginated response of notes api when there's no note present
        """

        # Delete all notes
        self.test_cleanup()

        # Get default page
        response = requests.get(self._get_url("api/v1/annotations"), params={"user": "dummy-user-id"})
        self.assertTrue(response.ok)
        self._verify_pagination_info(
            response=response.json(),
            total_notes=0,
            num_pages=0,
            notes_per_page=0,
            start=0,
            current_page=1,
            next_page=None,
            previous_page=None
        )

    def test_cleanup(self):
        response = requests.put(self._get_url("cleanup"))
        self.assertTrue(response.ok)
        self.assertEqual(len(self.server.get_all_notes()), 0)

    def test_create_notes(self):
        dummy_notes = self._get_dummy_notes(count=2)
        response = requests.post(self._get_url("create_notes"), data=json.dumps(dummy_notes))
        self.assertTrue(response.ok)
        self.assertEqual(len(self._get_notes()), 7)

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
        notes = self.server.get_all_notes()
        self.assertGreater(len(notes), 0, "Notes are empty.")
        return notes

    def _get_url(self, path):
        """
        Construt a URL to the stub EdxNotes service.
        """
        return "http://127.0.0.1:{port}/{path}/".format(
            port=self.server.port, path=path
        )
