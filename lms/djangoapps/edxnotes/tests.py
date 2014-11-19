"""
Tests for the EdxNotes app.
"""
import json
from mock import patch, MagicMock
from unittest import skipUnless
from datetime import datetime
from edxnotes.decorators import edxnotes
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured

from xmodule.tabs import EdxNotesTab
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.exceptions import ItemNotFoundError
from student.tests.factories import UserFactory
from . import helpers


@edxnotes
class TestProblem(object):
    """
    Test class (fake problem) decorated by edxnotes decorator.

    The purpose of this class is to imitate any problem.
    """
    def __init__(self, course):
        self.system = MagicMock(is_author_mode=False)
        self.scope_ids = MagicMock(usage_id="test_usage_id")
        self.runtime = MagicMock(course_id=course.id)
        self.descriptor = MagicMock()
        self.descriptor.runtime.modulestore.get_course.return_value = course

    def get_html(self):
        """
        Imitate get_html in module.
        """
        return 'original_get_html'


@skipUnless(settings.FEATURES["ENABLE_EDXNOTES"], 'EdxNotes feature needs to be enabled.')
class EdxNotesDecoratorTest(TestCase):
    """
    Tests for edxnotes decorator.
    """

    def setUp(self):
        self.course = CourseFactory.create(edxnotes=True)
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")
        self.problem = TestProblem(self.course)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_EDXNOTES': True})
    def test_edxnotes_enabled(self):
        """
        Tests if get_html is wrapped when feature flag is on.
        """
        self.course.tabs.append(EdxNotesTab())
        modulestore().update_item(self.course, self.user.id)
        self.assertIn('edx-notes-wrapper', self.problem.get_html())

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_EDXNOTES': True})
    def test_edxnotes_disabled_if_edxnotes_flag_is_false(self):
        """
        Tests if get_html is not wrapped when feature flag is off.
        """
        self.assertEqual('original_get_html', self.problem.get_html())

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_EDXNOTES': False})
    def test_edxnotes_disabled(self):
        """
        Tests if get_html is not wrapped when feature flag is off.
        """
        self.assertEqual('original_get_html', self.problem.get_html())

    def test_edxnotes_studio(self):
        """
        Tests if get_html is not wrapped when problem is rendered in Studio.
        """
        self.problem.system.is_author_mode = True
        self.assertEqual('original_get_html', self.problem.get_html())


@skipUnless(settings.FEATURES["ENABLE_EDXNOTES"], "EdxNotes feature needs to be enabled.")
class EdxNotesHelpersTest(TestCase):
    """
    Tests for EdxNotes helpers.
    """
    def setUp(self):
        """
        Setup a dummy course content.
        """
        self.course = CourseFactory.create()
        self.chapter = ItemFactory.create(category='chapter', parent_location=self.course.location)
        self.sequential = ItemFactory.create(category='sequential', parent_location=self.chapter.location)
        self.vertical = ItemFactory.create(category='vertical', parent_location=self.sequential.location)
        self.html_module_1 = ItemFactory.create(category='html', parent_location=self.vertical.location)
        self.html_module_2 = ItemFactory.create(category='html', parent_location=self.vertical.location)
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")
        self.datetimes = [
            datetime(2014, 11, 19, 8, 5, 16, 00000).isoformat(),
            datetime(2014, 11, 19, 8, 6, 16, 00000).isoformat(),
        ]
        self.datetimes_str = [
            "Nov 19, 2014 at 08:05 UTC",
            "Nov 19, 2014 at 08:06 UTC",
        ]

    def _get_jump_to_url(self, vertical):
        """
        Returns `jump_to` url for the `vertical`.
        """
        return reverse('jump_to', kwargs={
            'course_id': self.course.id.to_deprecated_string(),
            'location': vertical.location.to_deprecated_string(),
        })

    def _get_dummy_model(self, module, fields_to_update=None):
        """
        Returns dummy model for the `module`.
        """
        dummy_model = {
            u'quote': u'quote text',
            u'text': u'text',
            u'usage_id': unicode(module.location),
            u'updated': self.datetimes[0],
        }
        if fields_to_update:
            dummy_model.update(fields_to_update)
        return dummy_model

    def _get_dummy_note(self, module, vertical, fields_to_update=None):
        """
        Returns dummy note for the `module`.
        """
        dummy_note = {
            u'quote': u'quote text',
            u'text': u'text',
            u'unit': {
                u'url': self._get_jump_to_url(vertical),
                u'display_name': vertical.display_name_with_default,
            },
            u'usage_id': unicode(module.location),
            u'updated': self.datetimes_str[0],
        }

        if fields_to_update:
            dummy_note.update(fields_to_update)
        return dummy_note

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
        Tests that storage_url method returns correct values.
        """
        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com/"}):
            self.assertEqual("http://example.com/api/v1", helpers.get_endpoint())

        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com"}):
            self.assertEqual("http://example.com/api/v1", helpers.get_endpoint())

        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com"}):
            self.assertEqual("http://example.com/api/v1/some_path", helpers.get_endpoint("/some_path"))

        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": "http://example.com"}):
            self.assertEqual("http://example.com/api/v1/some_path", helpers.get_endpoint("some_path"))

        with patch.dict("django.conf.settings.EDXNOTES_INTERFACE", {"url": None}):
            self.assertRaises(ImproperlyConfigured, helpers.get_endpoint)

    @patch("edxnotes.helpers.requests.get")
    def test_get_notes_correct_data(self, mock_get):
        """
        Tests the result if correct data is received.
        """
        mock_get.return_value.content = json.dumps([
            self._get_dummy_model(self.html_module_1),
            self._get_dummy_model(self.html_module_2, fields_to_update={"updated": self.datetimes[1]}),
        ])

        self.assertItemsEqual([
            self._get_dummy_note(self.html_module_2, self.vertical, fields_to_update={"updated": self.datetimes_str[1]}),
            self._get_dummy_note(self.html_module_1, self.vertical),
        ], json.loads(helpers.get_notes(self.user, self.course)))

    @patch("edxnotes.helpers.requests.get")
    def test_get_notes_json_error(self, mock_get):
        """
        Tests the result if incorrect json us received.
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
    def test_get_notes_no_item(self, mock_get):
        """
        Tests the result if appropriate module is not found.
        """
        module = MagicMock()
        module.location = self.course.id.make_usage_key("html", "test_item")
        mock_get.return_value.content = json.dumps([
            self._get_dummy_model(self.html_module_1),
            self._get_dummy_model(module),
        ])

        self.assertItemsEqual([
            self._get_dummy_note(self.html_module_1, self.vertical),
        ], json.loads(helpers.get_notes(self.user, self.course)))

    @patch("edxnotes.helpers.requests.get")
    def test_get_notes_has_access(self, mock_get):
        """
        Tests the result if the user do not has access to some modules.
        """
        self.html_module_2.visible_to_staff_only = True
        modulestore().update_item(self.html_module_2, self.user.id)

        mock_get.return_value.content = json.dumps([
            self._get_dummy_model(self.html_module_1),
            self._get_dummy_model(self.html_module_2),
        ])
        self.assertItemsEqual([
            self._get_dummy_note(self.html_module_1, self.vertical),
        ], json.loads(helpers.get_notes(self.user, self.course)))

    def test_get_parent(self):
        """
        Tests `test_get_parent` method for the successful result.
        """
        parent = helpers.get_parent(modulestore(), self.html_module_1.location)
        self.assertEqual(parent.location, self.vertical.location)

    def test_get_parent_no_location(self):
        """
        Tests the result if parent location is not found.
        """
        store = MagicMock()
        store.get_parent_location.return_value = None
        self.assertEqual(helpers.get_parent(store, self.html_module_1.location), None)

    def test_get_parent_no_parent(self):
        """
        Tests the result if parent module is not found.
        """
        store = MagicMock()
        store.get_item.side_effect = ItemNotFoundError
        self.assertEqual(helpers.get_parent(store, self.html_module_1.location), None)

    def test_get_parent_context(self):
        """
        Tests `test_get_parent_context` method for the successful result.
        """
        self.assertDictEqual(
            helpers.get_parent_context(self.course, modulestore(), self.html_module_1.location),
            {
                u"url": self._get_jump_to_url(self.vertical),
                u"display_name": self.vertical.display_name_with_default,
            }

        )

    # pylint: disable=unused-argument
    @patch('edxnotes.helpers.get_parent', return_value=None)
    def test_get_parent_context_no_parent(self, mock_get_parent):
        """
        Tests the result if parent module is not found.
        """
        self.assertEqual(
            helpers.get_parent_context(self.course, modulestore(), self.html_module_1.location),
            {
                u"url": None,
                u"display_name": None,
            }
        )


@skipUnless(settings.FEATURES["ENABLE_EDXNOTES"], "EdxNotes feature needs to be enabled.")
class EdxNotesViewsTest(TestCase):
    """
    Tests for EdxNotes views.
    """
    def setUp(self):
        super(EdxNotesViewsTest, self).setUp()
        self.course = CourseFactory.create(edxnotes=True)
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")
        self.notes_page_url = reverse("edxnotes", args=[unicode(self.course.id)])

    # pylint: disable=unused-argument
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": True})
    @patch("edxnotes.views.get_notes", return_value=[])
    def test_edxnotes_view_is_enabled(self, mock_get_notes):
        """
        Tests that appropriate view is received if EdxNotes feature is enabled.
        """
        self.course.tabs.append(EdxNotesTab())
        modulestore().update_item(self.course, self.user.id)
        response = self.client.get(self.notes_page_url)
        self.assertContains(response, "<h1>Notes</h1>")

    # pylint: disable=unused-argument
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_EDXNOTES": False})
    @patch("edxnotes.views.get_notes", return_value=[])
    def test_edxnotes_view_is_disabled(self, mock_get_notes):
        """
        Tests that 404 response is received if EdxNotes feature is disabled.
        """
        response = self.client.get(self.notes_page_url)
        self.assertEqual(response.status_code, 404)
