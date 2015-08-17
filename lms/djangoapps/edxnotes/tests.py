"""
Tests for the EdxNotes app.
"""
from contextlib import contextmanager
import ddt
import json
import jwt
from mock import patch, MagicMock
from unittest import skipUnless
from datetime import datetime

from edxmako.shortcuts import render_to_string
from edxnotes import helpers
from edxnotes.decorators import edxnotes
from edxnotes.exceptions import EdxNotesParseError, EdxNotesServiceUnavailable
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.test.client import RequestFactory
from django.test.utils import override_settings
from oauth2_provider.tests.factories import ClientFactory
from provider.oauth2.models import Client
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.tabs import CourseTab
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from courseware.tabs import get_course_tab_list
from student.tests.factories import UserFactory, CourseEnrollmentFactory


def enable_edxnotes_for_the_course(course, user_id):
    """
    Enable EdxNotes for the course.
    """
    course.tabs.append(CourseTab.load("edxnotes"))
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
class EdxNotesDecoratorTest(ModuleStoreTestCase):
    """
    Tests for edxnotes decorator.
    """

    def setUp(self):
        super(EdxNotesDecoratorTest, self).setUp()

        ClientFactory(name="edx-notes")
        # Using old mongo because of locator comparison issues (see longer
        # note below in EdxNotesHelpersTest setUp.
        self.course = CourseFactory.create(edxnotes=True, default_store=ModuleStoreEnum.Type.mongo)
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")
        self.problem = TestProblem(self.course)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_EDXNOTES': True})
    @patch("edxnotes.decorators.get_public_endpoint")
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
            "edxnotes_visibility": "true",
            "params": {
                "usageId": u"test_usage_id",
                "courseId": unicode(self.course.id).encode("utf-8"),
                "token": "token",
                "tokenUrl": "/tokenUrl",
                "endpoint": "/endpoint",
                "debug": settings.DEBUG,
                "eventStringLimit": settings.TRACK_MAX_EVENT / 6,
            },
        }
        self.assertEqual(
            self.problem.get_html(),
            render_to_string("edxnotes_wrapper.html", expected_context),
        )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    def test_edxnotes_disabled_if_edxnotes_flag_is_false(self):
        """
        Tests that get_html is wrapped when feature flag is on, but edxnotes are
        disabled for the course.
        """
        self.assertEqual("original_get_html", self.problem.get_html())

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": False})
    def test_edxnotes_disabled(self):
        """
        Tests that get_html is not wrapped when feature flag is off.
        """
        self.assertEqual("original_get_html", self.problem.get_html())

    def test_edxnotes_studio(self):
        """
        Tests that get_html is not wrapped when problem is rendered in Studio.
        """
        self.problem.system.is_author_mode = True
        self.assertEqual("original_get_html", self.problem.get_html())

    def test_edxnotes_harvard_notes_enabled(self):
        """
        Tests that get_html is not wrapped when Harvard Annotation Tool is enabled.
        """
        self.course.advanced_modules = ["videoannotation", "imageannotation", "textannotation"]
        enable_edxnotes_for_the_course(self.course, self.user.id)
        self.assertEqual("original_get_html", self.problem.get_html())


@skipUnless(settings.FEATURES["ENABLE_EDXNOTES"], "EdxNotes feature needs to be enabled.")
@ddt.ddt
class EdxNotesHelpersTest(ModuleStoreTestCase):
    """
    Tests for EdxNotes helpers.
    """
    def setUp(self):
        """
        Setup a dummy course content.
        """
        super(EdxNotesHelpersTest, self).setUp()

        # There are many tests that are comparing locators as returned from helper methods. When using
        # the split modulestore, some of those locators have version and branch information, but the
        # comparison values do not. This needs further investigation in order to enable these tests
        # with the split modulestore.
        with self.store.default_store(ModuleStoreEnum.Type.mongo):
            ClientFactory(name="edx-notes")
            self.course = CourseFactory.create()
            self.chapter = ItemFactory.create(category="chapter", parent_location=self.course.location)
            self.chapter_2 = ItemFactory.create(category="chapter", parent_location=self.course.location)
            self.sequential = ItemFactory.create(category="sequential", parent_location=self.chapter.location)
            self.vertical = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
            self.html_module_1 = ItemFactory.create(category="html", parent_location=self.vertical.location)
            self.html_module_2 = ItemFactory.create(category="html", parent_location=self.vertical.location)
            self.vertical_with_container = ItemFactory.create(
                category='vertical', parent_location=self.sequential.location
            )
            self.child_container = ItemFactory.create(
                category='split_test', parent_location=self.vertical_with_container.location)
            self.child_vertical = ItemFactory.create(category='vertical', parent_location=self.child_container.location)
            self.child_html_module = ItemFactory.create(category="html", parent_location=self.child_vertical.location)

            # Read again so that children lists are accurate
            self.course = self.store.get_item(self.course.location)
            self.chapter = self.store.get_item(self.chapter.location)
            self.chapter_2 = self.store.get_item(self.chapter_2.location)
            self.sequential = self.store.get_item(self.sequential.location)
            self.vertical = self.store.get_item(self.vertical.location)

            self.vertical_with_container = self.store.get_item(self.vertical_with_container.location)
            self.child_container = self.store.get_item(self.child_container.location)
            self.child_vertical = self.store.get_item(self.child_vertical.location)
            self.child_html_module = self.store.get_item(self.child_html_module.location)

            self.user = UserFactory.create(username="Joe", email="joe@example.com", password="edx")
            self.client.login(username=self.user.username, password="edx")

    def _get_unit_url(self, course, chapter, section, position=1):
        """
        Returns `jump_to_id` url for the `vertical`.
        """
        return reverse('courseware_position', kwargs={
            'course_id': course.id,
            'chapter': chapter.url_name,
            'section': section.url_name,
            'position': position,
        })

    def test_edxnotes_not_enabled(self):
        """
        Tests that edxnotes are disabled when the course tab configuration does NOT
        contain a tab with type "edxnotes."
        """
        self.course.tabs = []
        self.assertFalse(helpers.is_feature_enabled(self.course))

    def test_edxnotes_harvard_notes_enabled(self):
        """
        Tests that edxnotes are disabled when Harvard Annotation Tool is enabled.
        """
        self.course.advanced_modules = ["foo", "imageannotation", "boo"]
        self.assertFalse(helpers.is_feature_enabled(self.course))

        self.course.advanced_modules = ["foo", "boo", "videoannotation"]
        self.assertFalse(helpers.is_feature_enabled(self.course))

        self.course.advanced_modules = ["textannotation", "foo", "boo"]
        self.assertFalse(helpers.is_feature_enabled(self.course))

        self.course.advanced_modules = ["textannotation", "videoannotation", "imageannotation"]
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

    @ddt.data(
        helpers.get_public_endpoint,
        helpers.get_internal_endpoint,
    )
    def test_get_endpoints(self, get_endpoint_function):
        """
        Test that the get_public_endpoint and get_internal_endpoint functions
        return appropriate values.
        """
        @contextmanager
        def patch_edxnotes_api_settings(url):
            """
            Convenience function for patching both EDXNOTES_PUBLIC_API and
            EDXNOTES_INTERNAL_API.
            """
            with override_settings(EDXNOTES_PUBLIC_API=url):
                with override_settings(EDXNOTES_INTERNAL_API=url):
                    yield

        # url ends with "/"
        with patch_edxnotes_api_settings("http://example.com/"):
            self.assertEqual("http://example.com/", get_endpoint_function())

        # url doesn't have "/" at the end
        with patch_edxnotes_api_settings("http://example.com"):
            self.assertEqual("http://example.com/", get_endpoint_function())

        # url with path that starts with "/"
        with patch_edxnotes_api_settings("http://example.com"):
            self.assertEqual("http://example.com/some_path/", get_endpoint_function("/some_path"))

        # url with path without "/"
        with patch_edxnotes_api_settings("http://example.com"):
            self.assertEqual("http://example.com/some_path/", get_endpoint_function("some_path/"))

        # url is not configured
        with patch_edxnotes_api_settings(None):
            self.assertRaises(ImproperlyConfigured, get_endpoint_function)

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
                    u"chapter": {
                        u"display_name": self.chapter.display_name_with_default,
                        u"index": 0,
                        u"location": unicode(self.chapter.location),
                        u"children": [unicode(self.sequential.location)]
                    },
                    u"section": {
                        u"display_name": self.sequential.display_name_with_default,
                        u"location": unicode(self.sequential.location),
                        u"children": [unicode(self.vertical.location), unicode(self.vertical_with_container.location)]
                    },
                    u"unit": {
                        u"url": self._get_unit_url(self.course, self.chapter, self.sequential),
                        u"display_name": self.vertical.display_name_with_default,
                        u"location": unicode(self.vertical.location),
                    },
                    u"usage_id": unicode(self.html_module_2.location),
                    u"updated": "Nov 19, 2014 at 08:06 UTC",
                },
                {
                    u"quote": u"quote text",
                    u"text": u"text",
                    u"chapter": {
                        u"display_name": self.chapter.display_name_with_default,
                        u"index": 0,
                        u"location": unicode(self.chapter.location),
                        u"children": [unicode(self.sequential.location)]
                    },
                    u"section": {
                        u"display_name": self.sequential.display_name_with_default,
                        u"location": unicode(self.sequential.location),
                        u"children": [
                            unicode(self.vertical.location),
                            unicode(self.vertical_with_container.location)]
                    },
                    u"unit": {
                        u"url": self._get_unit_url(self.course, self.chapter, self.sequential),
                        u"display_name": self.vertical.display_name_with_default,
                        u"location": unicode(self.vertical.location),
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
                        u"chapter": {
                            u"display_name": self.chapter.display_name_with_default,
                            u"index": 0,
                            u"location": unicode(self.chapter.location),
                            u"children": [unicode(self.sequential.location)]
                        },
                        u"section": {
                            u"display_name": self.sequential.display_name_with_default,
                            u"location": unicode(self.sequential.location),
                            u"children": [
                                unicode(self.vertical.location),
                                unicode(self.vertical_with_container.location)]
                        },
                        u"unit": {
                            u"url": self._get_unit_url(self.course, self.chapter, self.sequential),
                            u"display_name": self.vertical.display_name_with_default,
                            u"location": unicode(self.vertical.location),
                        },
                        u"usage_id": unicode(self.html_module_2.location),
                        u"updated": "Nov 19, 2014 at 08:06 UTC",
                    },
                    {
                        u"quote": u"quote text",
                        u"text": u"text",
                        u"chapter": {
                            u"display_name": self.chapter.display_name_with_default,
                            u"index": 0,
                            u"location": unicode(self.chapter.location),
                            u"children": [unicode(self.sequential.location)]
                        },
                        u"section": {
                            u"display_name": self.sequential.display_name_with_default,
                            u"location": unicode(self.sequential.location),
                            u"children": [
                                unicode(self.vertical.location),
                                unicode(self.vertical_with_container.location)]
                        },
                        u"unit": {
                            u"url": self._get_unit_url(self.course, self.chapter, self.sequential),
                            u"display_name": self.vertical.display_name_with_default,
                            u"location": unicode(self.vertical.location),
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

    def test_preprocess_collection_escaping(self):
        """
        Tests the result if appropriate module is not found.
        """
        initial_collection = [{
            u"quote": u"test <script>alert('test')</script>",
            u"text": u"text \"<>&'",
            u"usage_id": unicode(self.html_module_1.location),
            u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000).isoformat()
        }]

        self.assertItemsEqual(
            [{
                u"quote": u"test &lt;script&gt;alert('test')&lt;/script&gt;",
                u"text": u'text "&lt;&gt;&amp;\'',
                u"chapter": {
                    u"display_name": self.chapter.display_name_with_default,
                    u"index": 0,
                    u"location": unicode(self.chapter.location),
                    u"children": [unicode(self.sequential.location)]
                },
                u"section": {
                    u"display_name": self.sequential.display_name_with_default,
                    u"location": unicode(self.sequential.location),
                    u"children": [unicode(self.vertical.location), unicode(self.vertical_with_container.location)]
                },
                u"unit": {
                    u"url": self._get_unit_url(self.course, self.chapter, self.sequential),
                    u"display_name": self.vertical.display_name_with_default,
                    u"location": unicode(self.vertical.location),
                },
                u"usage_id": unicode(self.html_module_1.location),
                u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000),
            }],
            helpers.preprocess_collection(self.user, self.course, initial_collection)
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
                u"chapter": {
                    u"display_name": self.chapter.display_name_with_default,
                    u"index": 0,
                    u"location": unicode(self.chapter.location),
                    u"children": [unicode(self.sequential.location)]
                },
                u"section": {
                    u"display_name": self.sequential.display_name_with_default,
                    u"location": unicode(self.sequential.location),
                    u"children": [unicode(self.vertical.location), unicode(self.vertical_with_container.location)]
                },
                u"unit": {
                    u"url": self._get_unit_url(self.course, self.chapter, self.sequential),
                    u"display_name": self.vertical.display_name_with_default,
                    u"location": unicode(self.vertical.location),
                },
                u"usage_id": unicode(self.html_module_1.location),
                u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000),
            }],
            helpers.preprocess_collection(self.user, self.course, initial_collection)
        )

    def test_preprocess_collection_has_access(self):
        """
        Tests the result if the user does not have access to some of the modules.
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
        self.store.update_item(self.html_module_2, self.user.id)
        self.assertItemsEqual(
            [{
                u"quote": u"quote text",
                u"text": u"text",
                u"chapter": {
                    u"display_name": self.chapter.display_name_with_default,
                    u"index": 0,
                    u"location": unicode(self.chapter.location),
                    u"children": [unicode(self.sequential.location)]
                },
                u"section": {
                    u"display_name": self.sequential.display_name_with_default,
                    u"location": unicode(self.sequential.location),
                    u"children": [unicode(self.vertical.location), unicode(self.vertical_with_container.location)]
                },
                u"unit": {
                    u"url": self._get_unit_url(self.course, self.chapter, self.sequential),
                    u"display_name": self.vertical.display_name_with_default,
                    u"location": unicode(self.vertical.location),
                },
                u"usage_id": unicode(self.html_module_1.location),
                u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000),
            }],
            helpers.preprocess_collection(self.user, self.course, initial_collection)
        )

    @patch("edxnotes.helpers.has_access")
    @patch("edxnotes.helpers.modulestore")
    def test_preprocess_collection_no_unit(self, mock_modulestore, mock_has_access):
        """
        Tests the result if the unit does not exist.
        """
        store = MagicMock()
        store.get_item().get_parent.return_value = None
        mock_modulestore.return_value = store
        mock_has_access.return_value = True
        initial_collection = [{
            u"quote": u"quote text",
            u"text": u"text",
            u"usage_id": unicode(self.html_module_1.location),
            u"updated": datetime(2014, 11, 19, 8, 5, 16, 00000).isoformat(),
        }]

        self.assertItemsEqual(
            [], helpers.preprocess_collection(self.user, self.course, initial_collection)
        )

    def test_get_parent_unit(self):
        """
        Tests `get_parent_unit` method for the successful result.
        """
        parent = helpers.get_parent_unit(self.html_module_1)
        self.assertEqual(parent.location, self.vertical.location)

        parent = helpers.get_parent_unit(self.child_html_module)
        self.assertEqual(parent.location, self.vertical_with_container.location)

        self.assertIsNone(helpers.get_parent_unit(None))
        self.assertIsNone(helpers.get_parent_unit(self.course))
        self.assertIsNone(helpers.get_parent_unit(self.chapter))
        self.assertIsNone(helpers.get_parent_unit(self.sequential))

    def test_get_module_context_sequential(self):
        """
        Tests `get_module_context` method for the sequential.
        """
        self.assertDictEqual(
            {
                u"display_name": self.sequential.display_name_with_default,
                u"location": unicode(self.sequential.location),
                u"children": [unicode(self.vertical.location), unicode(self.vertical_with_container.location)],
            },
            helpers.get_module_context(self.course, self.sequential)
        )

    def test_get_module_context_html_component(self):
        """
        Tests `get_module_context` method for the components.
        """
        self.assertDictEqual(
            {
                u"display_name": self.html_module_1.display_name_with_default,
                u"location": unicode(self.html_module_1.location),
            },
            helpers.get_module_context(self.course, self.html_module_1)
        )

    def test_get_module_context_chapter(self):
        """
        Tests `get_module_context` method for the chapters.
        """
        self.assertDictEqual(
            {
                u"display_name": self.chapter.display_name_with_default,
                u"index": 0,
                u"location": unicode(self.chapter.location),
                u"children": [unicode(self.sequential.location)],
            },
            helpers.get_module_context(self.course, self.chapter)
        )
        self.assertDictEqual(
            {
                u"display_name": self.chapter_2.display_name_with_default,
                u"index": 1,
                u"location": unicode(self.chapter_2.location),
                u"children": [],
            },
            helpers.get_module_context(self.course, self.chapter_2)
        )

    @override_settings(EDXNOTES_PUBLIC_API="http://example.com")
    @override_settings(EDXNOTES_INTERNAL_API="http://example.com")
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
                "highlight": True,
                "highlight_tag": "span",
                "highlight_class": "note-highlight",
            }
        )

    @override_settings(EDXNOTES_PUBLIC_API="http://example.com")
    @override_settings(EDXNOTES_INTERNAL_API="http://example.com")
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

    def test_get_course_position_no_chapter(self):
        """
        Returns `None` if no chapter found.
        """
        mock_course_module = MagicMock()
        mock_course_module.position = 3
        mock_course_module.get_display_items.return_value = []
        self.assertIsNone(helpers.get_course_position(mock_course_module))

    def test_get_course_position_to_chapter(self):
        """
        Returns a position that leads to COURSE/CHAPTER if this isn't the users's
        first time.
        """
        mock_course_module = MagicMock(id=self.course.id, position=3)

        mock_chapter = MagicMock()
        mock_chapter.url_name = 'chapter_url_name'
        mock_chapter.display_name_with_default = 'Test Chapter Display Name'

        mock_course_module.get_display_items.return_value = [mock_chapter]

        self.assertEqual(helpers.get_course_position(mock_course_module), {
            'display_name': 'Test Chapter Display Name',
            'url': '/courses/{}/courseware/chapter_url_name/'.format(self.course.id),
        })

    def test_get_course_position_no_section(self):
        """
        Returns `None` if no section found.
        """
        mock_course_module = MagicMock(id=self.course.id, position=None)
        mock_course_module.get_display_items.return_value = [MagicMock()]
        self.assertIsNone(helpers.get_course_position(mock_course_module))

    def test_get_course_position_to_section(self):
        """
        Returns a position that leads to COURSE/CHAPTER/SECTION if this is the
        user's first time.
        """
        mock_course_module = MagicMock(id=self.course.id, position=None)

        mock_chapter = MagicMock()
        mock_chapter.url_name = 'chapter_url_name'
        mock_course_module.get_display_items.return_value = [mock_chapter]

        mock_section = MagicMock()
        mock_section.url_name = 'section_url_name'
        mock_section.display_name_with_default = 'Test Section Display Name'

        mock_chapter.get_display_items.return_value = [mock_section]
        mock_section.get_display_items.return_value = [MagicMock()]

        self.assertEqual(helpers.get_course_position(mock_course_module), {
            'display_name': 'Test Section Display Name',
            'url': '/courses/{}/courseware/chapter_url_name/section_url_name/'.format(self.course.id),
        })

    def test_get_index(self):
        """
        Tests `get_index` method returns unit url.
        """
        children = self.sequential.children
        self.assertEqual(0, helpers.get_index(unicode(self.vertical.location), children))
        self.assertEqual(1, helpers.get_index(unicode(self.vertical_with_container.location), children))


@skipUnless(settings.FEATURES["ENABLE_EDXNOTES"], "EdxNotes feature needs to be enabled.")
class EdxNotesViewsTest(ModuleStoreTestCase):
    """
    Tests for EdxNotes views.
    """
    def setUp(self):
        ClientFactory(name="edx-notes")
        super(EdxNotesViewsTest, self).setUp()
        self.course = CourseFactory.create(edxnotes=True)
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.client.login(username=self.user.username, password="edx")
        self.notes_page_url = reverse("edxnotes", args=[unicode(self.course.id)])
        self.search_url = reverse("search_notes", args=[unicode(self.course.id)])
        self.get_token_url = reverse("get_token", args=[unicode(self.course.id)])
        self.visibility_url = reverse("edxnotes_visibility", args=[unicode(self.course.id)])

    def _get_course_module(self):
        """
        Returns the course module.
        """
        field_data_cache = FieldDataCache([self.course], self.course.id, self.user)
        return get_module_for_descriptor(
            self.user, MagicMock(), self.course, field_data_cache, self.course.id, course=self.course
        )

    def test_edxnotes_tab(self):
        """
        Tests that edxnotes tab is shown only when the feature is enabled.
        """
        def has_notes_tab(user, course):
            """Returns true if the "Notes" tab is shown."""
            request = RequestFactory().request()
            request.user = user
            tabs = get_course_tab_list(request, course)
            return len([tab for tab in tabs if tab.type == 'edxnotes']) == 1

        self.assertFalse(has_notes_tab(self.user, self.course))
        enable_edxnotes_for_the_course(self.course, self.user.id)
        # disable course.edxnotes
        self.course.edxnotes = False
        self.assertFalse(has_notes_tab(self.user, self.course))

        # reenable course.edxnotes
        self.course.edxnotes = True
        self.assertTrue(has_notes_tab(self.user, self.course))

    # pylint: disable=unused-argument
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    @patch("edxnotes.views.get_notes", return_value=[])
    def test_edxnotes_view_is_enabled(self, mock_get_notes):
        """
        Tests that appropriate view is received if EdxNotes feature is enabled.
        """
        enable_edxnotes_for_the_course(self.course, self.user.id)
        response = self.client.get(self.notes_page_url)
        self.assertContains(response, 'Highlights and notes you\'ve made in course content')

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": False})
    def test_edxnotes_view_is_disabled(self):
        """
        Tests that 404 status code is received if EdxNotes feature is disabled.
        """
        response = self.client.get(self.notes_page_url)
        self.assertEqual(response.status_code, 404)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    @patch("edxnotes.views.get_notes")
    def test_edxnotes_view_404_service_unavailable(self, mock_get_notes):
        """
        Tests that 404 status code is received if EdxNotes service is unavailable.
        """
        mock_get_notes.side_effect = EdxNotesServiceUnavailable
        enable_edxnotes_for_the_course(self.course, self.user.id)
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
    def test_search_404_service_unavailable(self, mock_search):
        """
        Tests that 404 status code is received if EdxNotes service is unavailable.
        """
        mock_search.side_effect = EdxNotesServiceUnavailable
        enable_edxnotes_for_the_course(self.course, self.user.id)
        response = self.client.get(self.search_url, {"text": "test"})
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.content)

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

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    def test_get_id_token(self):
        """
        Test generation of ID Token.
        """
        response = self.client.get(self.get_token_url)
        self.assertEqual(response.status_code, 200)
        client = Client.objects.get(name='edx-notes')
        jwt.decode(response.content, client.client_secret, audience=client.client_id)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    def test_get_id_token_anonymous(self):
        """
        Test that generation of ID Token does not work for anonymous user.
        """
        self.client.logout()
        response = self.client.get(self.get_token_url)
        self.assertEqual(response.status_code, 302)

    def test_edxnotes_visibility(self):
        """
        Can update edxnotes_visibility value successfully.
        """
        enable_edxnotes_for_the_course(self.course, self.user.id)
        response = self.client.post(
            self.visibility_url,
            data=json.dumps({"visibility": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        course_module = self._get_course_module()
        self.assertFalse(course_module.edxnotes_visibility)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": False})
    def test_edxnotes_visibility_if_feature_is_disabled(self):
        """
        Tests that 404 response is received if EdxNotes feature is disabled.
        """
        response = self.client.post(self.visibility_url)
        self.assertEqual(response.status_code, 404)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    def test_edxnotes_visibility_invalid_json(self):
        """
        Tests that 400 response is received if invalid JSON is sent.
        """
        enable_edxnotes_for_the_course(self.course, self.user.id)
        response = self.client.post(
            self.visibility_url,
            data="string",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    def test_edxnotes_visibility_key_error(self):
        """
        Tests that 400 response is received if invalid data structure is sent.
        """
        enable_edxnotes_for_the_course(self.course, self.user.id)
        response = self.client.post(
            self.visibility_url,
            data=json.dumps({'test_key': 1}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
