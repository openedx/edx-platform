"""Tests for the lms module itself."""

import logging
import mimetypes

from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch

from edxmako import LOOKUP, add_lookup
from microsite_configuration import microsite
from openedx.features.course_experience import course_home_url_name
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

log = logging.getLogger(__name__)


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
        self.assertEqual(len([directory for directory in directories if 'external_module' in directory]), 1)

        # This should not clear the directories list
        microsite.enable_microsites(log)
        directories = LOOKUP['main'].directories
        self.assertEqual(len([directory for directory in directories if 'external_module' in directory]), 1)


@patch.dict('django.conf.settings.FEATURES', {'ENABLE_FEEDBACK_SUBMISSION': True})
class HelpModalTests(ModuleStoreTestCase):
    """Tests for the help modal"""
    def setUp(self):
        super(HelpModalTests, self).setUp()
        self.course = CourseFactory.create()

    def test_simple_test(self):
        """
        Simple test to make sure that you don't get a 500 error when the modal
        is enabled.
        """
        url = reverse(course_home_url_name(self.course.id), args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
