"""
Tests for the EdxNotes app.
"""
import json
from mock import patch, MagicMock
from unittest import skipUnless
from datetime import datetime
from edxmako.shortcuts import render_to_string
from edxnotes.decorators import edxnotes
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from oauth2_provider.tests.factories import ClientFactory

from xmodule.tabs import EdxNotesTab
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.exceptions import ItemNotFoundError
from student.tests.factories import UserFactory

from .exceptions import EdxNotesParseError
from . import helpers


def enable_edxnotes_for_the_course(course, user_id):
    """
    Enable EdxNotes for the course.
    """
    course.tabs.append(EdxNotesTab())
    modulestore().update_item(course, user_id)


@edxnotes
class TestProblem(object):
    """
    Test class (fake problem) decorated by edxnotes decorator.

    The purpose of this class is to imitate any problem.
    """
    def __init__(self, course):
        self.system = MagicMock(is_author_mode=False)
        self.scope_ids = MagicMock(usage_id="test_usage_id")
        self.user = UserFactory.create(username="Joe", email="joe@example.com", password="edx")
        self.runtime = MagicMock(course_id=course.id, get_real_user=lambda anon_id: self.user)
        self.descriptor = MagicMock()
        self.descriptor.runtime.modulestore.get_course.return_value = course

    def get_html(self):
        """
        Imitate get_html in module.
        """
        return "original_get_html"


@skipUnless(settings.FEATURES["ENABLE_EDXNOTES"], "EdxNotes feature needs to be enabled.")
class EdxNotesDecoratorTest(TestCase):
    """
    Tests for edxnotes decorator.
    """

    def setUp(self):
        ClientFactory(name="edx-notes")
        self.course = CourseFactory.create(edxnotes=True)
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")
        self.problem = TestProblem(self.course)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_EDXNOTES': True})
    @patch("edxnotes.decorators.get_endpoint")
    @patch("edxnotes.decorators.get_token_url")
    @patch("edxnotes.decorators.get_id_token")
    @patch("edxnotes.decorators.generate_uid")
    def test_edxnotes_enabled(self, mock_generate_uid, mock_get_id_token, mock_get_token_url, mock_get_endpoint):
        """
        Tests if get_html is wrapped when feature flag is on and edxnotes are
        enabled for the course.
        """
        mock_generate_uid.return_value = "uid"
        mock_get_id_token.return_value = "token"
        mock_get_token_url.return_value = "/tokenUrl"
        mock_get_endpoint.return_value = "/endpoint"
        enable_edxnotes_for_the_course(self.course, self.user.id)
        expected_context = {
            "content": "original_get_html",
            "uid": "uid",
            "params": {
                "usageId": u"test_usage_id",
                "courseId": unicode(self.course.id).encode("utf-8"),
                "token": "token",
                "tokenUrl": "/tokenUrl",
                "endpoint": "/endpoint",
                "debug": settings.DEBUG,
            },
        }
        self.assertEqual(
            self.problem.get_html(),
            render_to_string("edxnotes_wrapper.html", expected_context),
        )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    def test_edxnotes_disabled_if_edxnotes_flag_is_false(self):
        """
        Tests if get_html is wrapped when feature flag is on, but edxnotes are
        disabled for the course.
        """
        self.assertEqual("original_get_html", self.problem.get_html())

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": False})
    def test_edxnotes_disabled(self):
        """
        Tests if get_html is not wrapped when feature flag is off.
        """
        self.assertEqual("original_get_html", self.problem.get_html())

    def test_edxnotes_studio(self):
        """
        Tests if get_html is not wrapped when problem is rendered in Studio.
        """
        self.problem.system.is_author_mode = True
        self.assertEqual("original_get_html", self.problem.get_html())


@skipUnless(settings.FEATURES["ENABLE_EDXNOTES"], "EdxNotes feature needs to be enabled.")
class EdxNotesHelpersTest(TestCase):
    """
    Tests for EdxNotes helpers.
    """
    def setUp(self):
        """
        Setup a dummy course content.
        """
        ClientFactory(name="edx-notes")
        self.course = CourseFactory.create()
        self.chapter = ItemFactory.create(category="chapter", parent_location=self.course.location)
        self.sequential = ItemFactory.create(category="sequential", parent_location=self.chapter.location)
        self.vertical = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
        self.html_module_1 = ItemFactory.create(category="html", parent_location=self.vertical.location)
        self.html_module_2 = ItemFactory.create(category="html", parent_location=self.vertical.location)
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")

    def _get_jump_to_url(self, vertical):
        """
        Returns `jump_to` url for the `vertical`.
        """
        return reverse("jump_to", kwargs={
            "course_id": self.course.id.to_deprecated_string(),
            "location": vertical.location.to_deprecated_string(),
        })

    def test_edxnotes_not_enabled(self):
        """
        Tests that edxnotes are disabled when the course tab configuration does NOT
        contain a tab with type "edxnotes."
        """
        self.course.tabs = []
        self.assertFalse(helpers.is_feature_enabled(self.course))

    def test_edxnotes_enabled(self):
        """
        Tests that edxnotes are enabled when the course tab configuration contains
        a tab with type "edxnotes."
        """
        self.course.tabs = [{"type": "foo"},
                            {"name": "Notes", "type": "edxnotes"},
                            {"type": "bar"}]
        self.assertTrue(helpers.is_feature_enabled(self.course))

    def test_get_endpoint(self):
        """
        Tests that storage_url method returns appropriate values.
        """
        # url ends with "/"
        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com/"}):
            self.assertEqual("http://example.com/", helpers.get_endpoint())

        # url doesn't have "/" at the end
        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com"}):
            self.assertEqual("http://example.com/", helpers.get_endpoint())

        # url with path that starts with "/"
        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com"}):
            self.assertEqual("http://example.com/some_path/", helpers.get_endpoint("/some_path"))

        # url with path without "/"
        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com"}):
            self.assertEqual("http://example.com/some_path/", helpers.get_endpoint("some_path/"))

        # url is not configured
        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": None}):
            self.assertRaises(ImproperlyConfigured, helpers.get_endpoint)

    @patch("edxnotes.helpers.requests.get")
    def test_get_notes_correct_data(self, mock_get):
        """
        Tests the result if correct data is received.
        """
        mock_get.return_value.content = json.dumps([
            {
                u"quote": u"quote text",
                u"text": u"text",
                u"usage_id": unicode(self.html_module_1.location),
                u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000).isoformat(),
            },
            {
                u"quote": u"quote text",
                u"text": u"text",
                u"usage_id": unicode(self.html_module_2.location),
                u"updated": datetime(2014, 11, 19, 8, 6, 16, 00000).isoformat(),
            }
        ])

        self.assertItemsEqual(
            [
                {
                    u"quote": u"quote text",
                    u"text": u"text",
                    u"unit": {
                        u"url": self._get_jump_to_url(self.vertical),
                        u"display_name": self.vertical.display_name_with_default,
                    },
                    u"usage_id": unicode(self.html_module_2.location),
                    u"updated": "Nov 19, 2014 at 08:06 UTC",
                },
                {
                    u"quote": u"quote text",
                    u"text": u"text",
                    u"unit": {
                        u"url": self._get_jump_to_url(self.vertical),
                        u"display_name": self.vertical.display_name_with_default,
                    },
                    u"usage_id": unicode(self.html_module_1.location),
                    u"updated": "Nov 19, 2014 at 08:05 UTC",
                },
            ],
            json.loads(helpers.get_notes(self.user, self.course))
        )

    @patch("edxnotes.helpers.requests.get")
    def test_get_notes_json_error(self, mock_get):
        """
        Tests the result if incorrect json is received.
        """
        mock_get.return_value.content = "Error"
        self.assertIsNone(helpers.get_notes(self.user, self.course))

    @patch("edxnotes.helpers.requests.get")
    def test_get_notes_empty_collection(self, mock_get):
        """
        Tests the result if an empty collection is received.
        """
        mock_get.return_value.content = json.dumps([])
        self.assertIsNone(helpers.get_notes(self.user, self.course))

    @patch("edxnotes.helpers.requests.get")
    def test_search_correct_data(self, mock_get):
        """
        Tests the result if correct data is received.
        """
        mock_get.return_value.content = json.dumps({
            "total": 2,
            "rows": [
                {
                    u"quote": u"quote text",
                    u"text": u"text",
                    u"usage_id": unicode(self.html_module_1.location),
                    u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000).isoformat(),
                },
                {
                    u"quote": u"quote text",
                    u"text": u"text",
                    u"usage_id": unicode(self.html_module_2.location),
                    u"updated": datetime(2014, 11, 19, 8, 6, 16, 00000).isoformat(),
                }
            ]
        })

        self.assertItemsEqual(
            {
                "total": 2,
                "rows": [
                    {
                        u"quote": u"quote text",
                        u"text": u"text",
                        u"unit": {
                            u"url": self._get_jump_to_url(self.vertical),
                            u"display_name": self.vertical.display_name_with_default,
                        },
                        u"usage_id": unicode(self.html_module_2.location),
                        u"updated": "Nov 19, 2014 at 08:06 UTC",
                    },
                    {
                        u"quote": u"quote text",
                        u"text": u"text",
                        u"unit": {
                            u"url": self._get_jump_to_url(self.vertical),
                            u"display_name": self.vertical.display_name_with_default,
                        },
                        u"usage_id": unicode(self.html_module_1.location),
                        u"updated": "Nov 19, 2014 at 08:05 UTC",
                    },
                ]
            },
            json.loads(helpers.search(self.user, self.course, "test"))
        )

    @patch("edxnotes.helpers.requests.get")
    def test_search_json_error(self, mock_get):
        """
        Tests the result if incorrect json is received.
        """
        mock_get.return_value.content = "Error"
        self.assertRaises(EdxNotesParseError, helpers.search, self.user, self.course, "test")

    @patch("edxnotes.helpers.requests.get")
    def test_search_wrong_data_format(self, mock_get):
        """
        Tests the result if incorrect data structure is received.
        """
        mock_get.return_value.content = json.dumps({"1": 2})
        self.assertRaises(EdxNotesParseError, helpers.search, self.user, self.course, "test")

    @patch("edxnotes.helpers.requests.get")
    def test_search_empty_collection(self, mock_get):
        """
        Tests no results.
        """
        mock_get.return_value.content = json.dumps({
            "total": 0,
            "rows": []
        })
        self.assertItemsEqual(
            {
                "total": 0,
                "rows": []
            },
            json.loads(helpers.search(self.user, self.course, "test"))
        )

    def test_preprocess_collection_no_item(self):
        """
        Tests the result if appropriate module is not found.
        """
        initial_collection = [
            {
                u"quote": u"quote text",
                u"text": u"text",
                u"usage_id": unicode(self.html_module_1.location),
                u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000).isoformat()
            },
            {
                u"quote": u"quote text",
                u"text": u"text",
                u"usage_id": unicode(self.course.id.make_usage_key("html", "test_item")),
                u"updated": datetime(2014, 11, 19, 8, 6, 16, 00000).isoformat()
            },
        ]

        self.assertItemsEqual(
            [{
                u"quote": u"quote text",
                u"text": u"text",
                u"unit": {
                    u"url": self._get_jump_to_url(self.vertical),
                    u"display_name": self.vertical.display_name_with_default,
                },
                u"usage_id": unicode(self.html_module_1.location),
                u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000),
            }],
            helpers.preprocess_collection(self.user, self.course, initial_collection)
        )

    def test_preprocess_collection_has_access(self):
        """
        Tests the result if the user do not has access to some modules.
        """
        initial_collection = [
            {
                u"quote": u"quote text",
                u"text": u"text",
                u"usage_id": unicode(self.html_module_1.location),
                u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000).isoformat(),
            },
            {
                u"quote": u"quote text",
                u"text": u"text",
                u"usage_id": unicode(self.html_module_2.location),
                u"updated": datetime(2014, 11, 19, 8, 6, 16, 00000).isoformat(),
            },
        ]
        self.html_module_2.visible_to_staff_only = True
        modulestore().update_item(self.html_module_2, self.user.id)
        self.assertItemsEqual(
            [{
                u"quote": u"quote text",
                u"text": u"text",
                u"unit": {
                    u"url": self._get_jump_to_url(self.vertical),
                    u"display_name": self.vertical.display_name_with_default,
                },
                u"usage_id": unicode(self.html_module_1.location),
                u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000),
            }],
            helpers.preprocess_collection(self.user, self.course, initial_collection)
        )

    def test_get_ancestor(self):
        """
        Tests `test_get_ancestor` method for the successful result.
        """
        parent = helpers.get_ancestor(modulestore(), self.html_module_1.location)
        self.assertEqual(parent.location, self.vertical.location)

    def test_get_ancestor_no_location(self):
        """
        Tests the result if parent location is not found.
        """
        store = MagicMock()
        store.get_parent_location.return_value = None
        self.assertEqual(helpers.get_ancestor(store, self.html_module_1.location), None)

    def test_get_ancestor_no_parent(self):
        """
        Tests the result if ancestor module is not found.
        """
        store = MagicMock()
        store.get_item.side_effect = ItemNotFoundError
        self.assertEqual(helpers.get_ancestor(store, self.html_module_1.location), None)

    def test_get_ancestor_context(self):
        """
        Tests `test_get_ancestor_context` method for the successful result.
        """
        self.assertDictEqual(
            {
                u"url": self._get_jump_to_url(self.vertical),
                u"display_name": self.vertical.display_name_with_default,
            },
            helpers.get_ancestor_context(self.course, modulestore(), self.html_module_1.location)
        )

    # pylint: disable=unused-argument
    @patch("edxnotes.helpers.get_ancestor", return_value=None)
    def test_get_ancestor_context_no_parent(self, mock_get_ancestor):
        """
        Tests the result if parent module is not found.
        """
        self.assertEqual(
            {
                u"url": None,
                u"display_name": None,
            },
            helpers.get_ancestor_context(self.course, modulestore(), self.html_module_1.location)
        )

    @patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com"})
    @patch("edxnotes.helpers.anonymous_id_for_user")
    @patch("edxnotes.helpers.get_id_token")
    @patch("edxnotes.helpers.requests.get")
    def test_send_request_with_query_string(self, mock_get, mock_get_id_token, mock_anonymous_id_for_user):
        """
        Tests that requests are send with correct information.
        """
        mock_get_id_token.return_value = "test_token"
        mock_anonymous_id_for_user.return_value = "anonymous_id"
        helpers.send_request(
            self.user, self.course.id, path="test", query_string="text"
        )
        mock_get.assert_called_with(
            "http://example.com/test/",
            headers={
                "x-annotator-auth-token": "test_token"
            },
            params={
                "user": "anonymous_id",
                "course_id": unicode(self.course.id),
                "text": "text",
            }
        )

    @patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com"})
    @patch("edxnotes.helpers.anonymous_id_for_user")
    @patch("edxnotes.helpers.get_id_token")
    @patch("edxnotes.helpers.requests.get")
    def test_send_request_without_query_string(self, mock_get, mock_get_id_token, mock_anonymous_id_for_user):
        """
        Tests that requests are send with correct information.
        """
        mock_get_id_token.return_value = "test_token"
        mock_anonymous_id_for_user.return_value = "anonymous_id"
        helpers.send_request(
            self.user, self.course.id, path="test"
        )
        mock_get.assert_called_with(
            "http://example.com/test/",
            headers={
                "x-annotator-auth-token": "test_token"
            },
            params={
                "user": "anonymous_id",
                "course_id": unicode(self.course.id),
            }
        )


@skipUnless(settings.FEATURES["ENABLE_EDXNOTES"], "EdxNotes feature needs to be enabled.")
class EdxNotesViewsTest(TestCase):
    """
    Tests for EdxNotes views.
    """
    def setUp(self):
        ClientFactory(name="edx-notes")
        super(EdxNotesViewsTest, self).setUp()
        self.course = CourseFactory.create(edxnotes=True)
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")
        self.notes_page_url = reverse("edxnotes", args=[unicode(self.course.id)])
        self.search_url = reverse("search_notes", args=[unicode(self.course.id)])

    # pylint: disable=unused-argument
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    @patch("edxnotes.views.get_notes", return_value=[])
    def test_edxnotes_view_is_enabled(self, mock_get_notes):
        """
        Tests that appropriate view is received if EdxNotes feature is enabled.
        """
        enable_edxnotes_for_the_course(self.course, self.user.id)
        response = self.client.get(self.notes_page_url)
        self.assertContains(response, "<h1>Notes</h1>")

    # pylint: disable=unused-argument
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": False})
    def test_edxnotes_view_is_disabled(self):
        """
        Tests that 404 status code is received if EdxNotes feature is disabled.
        """
        response = self.client.get(self.notes_page_url)
        self.assertEqual(response.status_code, 404)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    @patch("edxnotes.views.search")
    def test_search_notes_successfully_respond(self, mock_search):
        """
        Tests that `search_notes` successfully respond if EdxNotes feature is enabled.
        """
        mock_search.return_value = json.dumps({
            "total": 0,
            "rows": [],
        })
        enable_edxnotes_for_the_course(self.course, self.user.id)
        response = self.client.get(self.search_url, {"text": "test"})
        self.assertEqual(json.loads(response.content), {
            "total": 0,
            "rows": [],
        })
        self.assertEqual(response.status_code, 200)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": False})
    @patch("edxnotes.views.search")
    def test_search_notes_is_disabled(self, mock_search):
        """
        Tests that 404 status code is received if EdxNotes feature is disabled.
        """
        mock_search.return_value = json.dumps({
            "total": 0,
            "rows": [],
        })
        response = self.client.get(self.search_url, {"text": "test"})
        self.assertEqual(response.status_code, 404)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    @patch("edxnotes.views.search")
    def test_search_notes_without_required_parameters(self, mock_search):
        """
        Tests that 400 status code is received if the required parameters were not sent.
        """
        mock_search.return_value = json.dumps({
            "total": 0,
            "rows": [],
        })
        enable_edxnotes_for_the_course(self.course, self.user.id)
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 400)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    @patch("edxnotes.views.search")
    def test_search_notes_exception(self, mock_search):
        """
        Tests that 500 status code is received if invalid data was received from
        EdXNotes service.
        """
        mock_search.side_effect = EdxNotesParseError
        enable_edxnotes_for_the_course(self.course, self.user.id)
        response = self.client.get(self.search_url, {"text": "test"})
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.content)
