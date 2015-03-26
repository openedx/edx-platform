"""Tests for the lms module itself."""

import mimetypes
from mock import patch

from django.test import TestCase
from django.core.urlresolvers import reverse

from edxmako import add_lookup, LOOKUP
from lms import startup
from xmodule.modulestore.tests.factories import CourseFactory
from util import keyword_substitution


class LmsModuleTests(TestCase):
    """
    Tests for lms module itself.
    """

    def test_new_mimetypes(self):
        extensions = ['eot', 'otf', 'ttf', 'woff']
        for extension in extensions:
            mimetype, _ = mimetypes.guess_type('test.' + extension)
            self.assertIsNotNone(mimetype)


class TemplateLookupTests(TestCase):
    """
    Tests for TemplateLookup.
    """

    def test_add_lookup_to_main(self):
        """Test that any template directories added are not cleared when microsites are enabled."""

        add_lookup('main', 'external_module', __name__)
        directories = LOOKUP['main'].directories
        self.assertEqual(len([dir for dir in directories if 'external_module' in dir]), 1)

        # This should not clear the directories list
        startup.enable_microsites()
        directories = LOOKUP['main'].directories
        self.assertEqual(len([dir for dir in directories if 'external_module' in dir]), 1)


@patch.dict('django.conf.settings.FEATURES', {'ENABLE_FEEDBACK_SUBMISSION': True})
class HelpModalTests(TestCase):
    """Tests for the help modal"""
    def setUp(self):
        self.course = CourseFactory.create()

    def test_simple_test(self):
        """
        Simple test to make sure that you don't get a 500 error when the modal
        is enabled.
        """
        url = reverse('info', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)


class KeywordSubConfigTests(TestCase):
    """ Tests for configuring keyword substitution feature """

    def test_keyword_map_not_empty(self):
        """ Ensure that the keyword subsitution map is non-empty """
        self.assertFalse(keyword_substitution.keyword_function_map_is_empty())

    def test_adding_keyword_map_is_noop(self):
        """ Test that trying to add a new keyword mapping is a no-op """

        existing_map = keyword_substitution.KEYWORD_FUNCTION_MAP
        keyword_substitution.add_keyword_function_map({
            '%%USER_ID%%': lambda x: x,
            '%%USER_FULLNAME%%': lambda x: x,
        })
        self.assertDictEqual(existing_map, keyword_substitution.KEYWORD_FUNCTION_MAP)
