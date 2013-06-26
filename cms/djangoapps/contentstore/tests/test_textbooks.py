import json
from unittest import TestCase
from .utils import CourseTestCase
from django.core.urlresolvers import reverse
from contentstore.utils import get_modulestore
from xmodule.modulestore.inheritance import own_metadata

from contentstore.views.course import (
    validate_textbooks_json, validate_textbook_json, TextbookValidationError)


class TextbookIndexTestCase(CourseTestCase):
    def setUp(self):
        super(TextbookIndexTestCase, self).setUp()
        self.url = reverse('textbook_index', kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name,
        })

    def test_view_index(self):
        resp = self.client.get(self.url)
        self.assert2XX(resp.status_code)
        # we don't have resp.context right now,
        # due to bugs in our testing harness :(
        if resp.context:
            self.assertEqual(resp.context['course'], self.course)

    def test_view_index_xhr(self):
        resp = self.client.get(
            self.url,
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assert2XX(resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual(self.course.pdf_textbooks, obj)

    def test_view_index_xhr_post(self):
        textbooks = [
            {"tab_title": "Hi, mom!"},
            {"tab_title": "Textbook 2"},
        ]
        resp = self.client.post(
            self.url,
            data=json.dumps(textbooks),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assert2XX(resp.status_code)

        # reload course
        store = get_modulestore(self.course.location)
        course = store.get_item(self.course.location)
        # should be the same, except for added ID
        no_ids = []
        for textbook in course.pdf_textbooks:
            del textbook["id"]
            no_ids.append(textbook)
        self.assertEqual(no_ids, textbooks)

    def test_view_index_xhr_post_invalid(self):
        resp = self.client.post(
            self.url,
            data="invalid",
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assert4XX(resp.status_code)
        obj = json.loads(resp.content)
        self.assertIn("error", obj)


class TextbookCreateTestCase(CourseTestCase):
    def setUp(self):
        super(TextbookCreateTestCase, self).setUp()
        self.url = reverse('create_textbook', kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name,
        })
        self.textbook = {
            "tab_title": "Economics",
            "chapters": {
                "title": "Chapter 1",
                "url": "/a/b/c/ch1.pdf",
            }
        }

    def test_happy_path(self):
        resp = self.client.post(
            self.url,
            data=json.dumps(self.textbook),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn("Location", resp)
        textbook = json.loads(resp.content)
        self.assertIn("id", textbook)
        del textbook["id"]
        self.assertEqual(self.textbook, textbook)

    def test_get(self):
        resp = self.client.get(
            self.url,
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 405)

    def test_valid_id(self):
        self.textbook["id"] = "7x5"
        resp = self.client.post(
            self.url,
            data=json.dumps(self.textbook),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 201)
        textbook = json.loads(resp.content)
        self.assertEqual(self.textbook, textbook)

    def test_invalid_id(self):
        self.textbook["id"] = "xxx"
        resp = self.client.post(
            self.url,
            data=json.dumps(self.textbook),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assert4XX(resp.status_code)
        self.assertNotIn("Location", resp)


class TextbookByIdTestCase(CourseTestCase):
    def setUp(self):
        super(TextbookByIdTestCase, self).setUp()
        self.textbook1 = {
            "tab_title": "Economics",
            "id": 1,
            "chapters": {
                "title": "Chapter 1",
                "url": "/a/b/c/ch1.pdf",
            }
        }
        self.url1 = reverse('textbook_by_id', kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name,
            'tid': 1,
        })
        self.textbook2 = {
            "tab_title": "Algebra",
            "id": 2,
            "chapters": {
                "title": "Chapter 11",
                "url": "/a/b/ch11.pdf",
            }
        }
        self.url2 = reverse('textbook_by_id', kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name,
            'tid': 2,
        })
        self.course.pdf_textbooks = [self.textbook1, self.textbook2]
        self.store = get_modulestore(self.course.location)
        self.store.update_metadata(self.course.location, own_metadata(self.course))
        self.url_nonexist = reverse('textbook_by_id', kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name,
            'tid': 20,
        })

    def test_get_1(self):
        resp = self.client.get(self.url1)
        self.assert2XX(resp.status_code)
        compare = json.loads(resp.content)
        self.assertEqual(compare, self.textbook1)

    def test_get_2(self):
        resp = self.client.get(self.url2)
        self.assert2XX(resp.status_code)
        compare = json.loads(resp.content)
        self.assertEqual(compare, self.textbook2)

    def test_get_nonexistant(self):
        resp = self.client.get(self.url_nonexist)
        self.assertEqual(resp.status_code, 404)

    def test_delete(self):
        resp = self.client.delete(self.url1)
        self.assert2XX(resp.status_code)
        course = self.store.get_item(self.course.location)
        self.assertEqual(course.pdf_textbooks, [self.textbook2])

    def test_delete_nonexistant(self):
        resp = self.client.delete(self.url_nonexist)
        self.assertEqual(resp.status_code, 404)
        course = self.store.get_item(self.course.location)
        self.assertEqual(course.pdf_textbooks, [self.textbook1, self.textbook2])

    def test_create_new_by_id(self):
        textbook = {
            "tab_title": "a new textbook",
            "url": "supercool.pdf",
            "id": "1supercool",
        }
        url = reverse("textbook_by_id", kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name,
            'tid': "1supercool",
        })
        resp = self.client.post(
            url,
            data=json.dumps(textbook),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        resp2 = self.client.get(url)
        self.assert2XX(resp2.status_code)
        compare = json.loads(resp2.content)
        self.assertEqual(compare, textbook)
        course = self.store.get_item(self.course.location)
        self.assertEqual(
            course.pdf_textbooks,
            [self.textbook1, self.textbook2, textbook]
        )

    def test_replace_by_id(self):
        replacement = {
            "tab_title": "You've been replaced!",
            "url": "supercool.pdf",
            "id": "2",
        }
        resp = self.client.post(
            self.url2,
            data=json.dumps(replacement),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        resp2 = self.client.get(self.url2)
        self.assert2XX(resp2.status_code)
        compare = json.loads(resp2.content)
        self.assertEqual(compare, replacement)
        course = self.store.get_item(self.course.location)
        self.assertEqual(
            course.pdf_textbooks,
            [self.textbook1, replacement]
        )


class TextbookValidationTestCase(TestCase):
    def setUp(self):
        self.tb1 = {
            "tab_title": "Hi, mom!",
            "url": "/mom.pdf"
        }
        self.tb2 = {
            "tab_title": "Hi, dad!",
            "chapters": [
                {
                    "title": "Baseball",
                    "url": "baseball.pdf",
                }, {
                    "title": "Basketball",
                    "url": "crazypants.pdf",
                }
            ]
        }
        self.textbooks = [self.tb1, self.tb2]

    def test_happy_path_plural(self):
        result = validate_textbooks_json(json.dumps(self.textbooks))
        self.assertEqual(self.textbooks, result)

    def test_happy_path_singular_1(self):
        result = validate_textbook_json(json.dumps(self.tb1))
        self.assertEqual(self.tb1, result)

    def test_happy_path_singular_2(self):
        result = validate_textbook_json(json.dumps(self.tb2))
        self.assertEqual(self.tb2, result)

    def test_valid_id(self):
        self.tb1["id"] = 1
        result = validate_textbook_json(json.dumps(self.tb1))
        self.assertEqual(self.tb1, result)

    def test_invalid_id(self):
        self.tb1["id"] = "abc"
        with self.assertRaises(TextbookValidationError):
            validate_textbook_json(json.dumps(self.tb1))

    def test_invalid_json_plural(self):
        with self.assertRaises(TextbookValidationError):
            validate_textbooks_json("[{'abc'}]")

    def test_invalid_json_singular(self):
        with self.assertRaises(TextbookValidationError):
            validate_textbook_json("[{1]}")

    def test_wrong_json_plural(self):
        with self.assertRaises(TextbookValidationError):
            validate_textbooks_json('{"tab_title": "Hi, mom!"}')

    def test_wrong_json_singular(self):
        with self.assertRaises(TextbookValidationError):
            validate_textbook_json('[{"tab_title": "Hi, mom!"}, {"tab_title": "Hi, dad!"}]')

    def test_no_tab_title_plural(self):
        with self.assertRaises(TextbookValidationError):
            validate_textbooks_json('[{"url": "/textbook.pdf"}]')

    def test_no_tab_title_singular(self):
        with self.assertRaises(TextbookValidationError):
            validate_textbook_json('{"url": "/textbook.pdf"}')

    def test_duplicate_ids(self):
        textbooks = [{
            "tab_title": "name one",
            "url": "one.pdf",
            "id": 1,
        }, {
            "tab_title": "name two",
            "url": "two.pdf",
            "id": 1,
        }]
        with self.assertRaises(TextbookValidationError):
            validate_textbooks_json(json.dumps(textbooks))
