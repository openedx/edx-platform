import json
import mock
from unittest import TestCase
from .utils import CourseTestCase
from django.core.urlresolvers import reverse
from contentstore.utils import get_modulestore

from contentstore.views.course import (
    validate_textbook_json, TextbookValidationError)


class TextbookTestCase(CourseTestCase):
    def setUp(self):
        super(TextbookTestCase, self).setUp()
        self.url = reverse('textbook_index', kwargs={
            'org': self.course.location.org,
            'course': self.course.location.course,
            'name': self.course.location.name,
        })

    def test_view_index(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
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
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(self.course.pdf_textbooks, obj)

    def test_view_index_xhr_post(self):
        textbooks = [
            {"tab_title": "Hi, mom!"},
            {"tab_title": "Textbook 2"},
        ]
        # import nose; nose.tools.set_trace()
        resp = self.client.post(
            self.url,
            data=json.dumps(textbooks),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, "")

        # reload course
        store = get_modulestore(self.course.location)
        course = store.get_item(self.course.location)
        self.assertEqual(course.pdf_textbooks, textbooks)


class TextbookValidationTestCase(TestCase):
    def test_happy_path(self):
        textbooks = [
            {
                "tab_title": "Hi, mom!",
                "url": "/mom.pdf"
            },
            {
                "tab_title": "Textbook 2",
                "chapters": [
                    {
                        "title": "Chapter 1",
                        "url": "/ch1.pdf"
                    }, {
                        "title": "Chapter 2",
                        "url": "/ch2.pdf"
                    }
                ]
            }
        ]

        result = validate_textbook_json(json.dumps(textbooks))
        self.assertEqual(textbooks, result)

    def test_invalid_json(self):
        with self.assertRaises(TextbookValidationError):
            validate_textbook_json("[{'abc'}]")

    def test_wrong_json(self):
        with self.assertRaises(TextbookValidationError):
            validate_textbook_json('{"tab_title": "Hi, mom!"}')

    def test_no_tab_title(self):
        with self.assertRaises(TextbookValidationError):
            validate_textbook_json('[{"url": "/textbook.pdf"}')
