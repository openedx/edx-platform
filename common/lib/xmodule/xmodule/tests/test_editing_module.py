""" Tests for editing descriptors"""
import unittest
import os
import logging

from mock import Mock
from pkg_resources import resource_string
from xmodule.editing_module import TabsEditingDescriptor
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.tests import get_test_descriptor_system

log = logging.getLogger(__name__)


class TabsEditingDescriptorTestCase(unittest.TestCase):
    """ Testing TabsEditingDescriptor"""

    def setUp(self):
        super(TabsEditingDescriptorTestCase, self).setUp()
        system = get_test_descriptor_system()
        system.render_template = Mock(return_value="<div>Test Template HTML</div>")
        self.tabs = [
            {
                'name': "Test_css",
                'template': "tabs/codemirror-edit.html",
                'current': True,
                'css': {
                    'scss': [resource_string(__name__,
                    '../../test_files/test_tabseditingdescriptor.scss')],
                    'css': [resource_string(__name__,
                    '../../test_files/test_tabseditingdescriptor.css')]
                }
            },
            {
                'name': "Subtitles",
                'template': "video/subtitles.html",
            },
            {
                'name': "Settings",
                'template': "tabs/video-metadata-edit-tab.html"
            }
        ]

        TabsEditingDescriptor.tabs = self.tabs
        self.descriptor = system.construct_xblock_from_class(
            TabsEditingDescriptor,
            scope_ids=ScopeIds(None, None, None, None),
            field_data=DictFieldData({}),
        )

    def test_get_css(self):
        """test get_css"""
        css = self.descriptor.get_css()
        test_files_dir = os.path.dirname(__file__).replace('xmodule/tests', 'test_files')
        test_css_file = os.path.join(test_files_dir, 'test_tabseditingdescriptor.scss')
        with open(test_css_file) as new_css:
            added_css = new_css.read()
        self.assertEqual(css['scss'].pop(), added_css)
        self.assertEqual(css['css'].pop(), added_css)

    def test_get_context(self):
        """"test get_context"""
        rendered_context = self.descriptor.get_context()
        self.assertListEqual(rendered_context['tabs'], self.tabs)

