# -*- coding: utf-8 -*-
"""Test for Video Alpha Xmodule functional logic.
These tests data readed from  xml or from mongo.

we have a ModuleStoreTestCase class defined in
common/lib/xmodule/xmodule/modulestore/tests/django_utils.py. You can
search for usages of this in the cms and lms tests for examples. You use
this so that it will do things like point the modulestore setting to mongo,
flush the contentstore before and after, load the templates, etc.
You can then use the CourseFactory and XModuleItemFactory as defined
in common/lib/xmodule/xmodule/modulestore/tests/factories.py to create
the course, section, subsection, unit, etc.
"""

import unittest
from xmodule.videoalpha_module import VideoAlphaDescriptor
from . import LogicTest
from lxml import etree
from pkg_resources import resource_string
from .import get_test_system

class VideoAlphaModuleTest(LogicTest):
    """Logic tests for VideoAlpha Xmodule."""
    descriptor_class = VideoAlphaDescriptor

    raw_model_data = {
        'data': '<videoalpha />'
    }

    def test_get_timeframe_no_parameters(self):
        "Make sure that timeframe() works correctly w/o parameters"
        xmltree = etree.fromstring('<videoalpha>test</videoalpha>')
        output = self.xmodule.get_timeframe(xmltree)
        self.assertEqual(output, ('', ''))

    def test_get_timeframe_with_one_parameter(self):
        "Make sure that timeframe() works correctly with one parameter"
        xmltree = etree.fromstring(
            '<videoalpha start_time="00:04:07">test</videoalpha>'
        )
        output = self.xmodule.get_timeframe(xmltree)
        self.assertEqual(output, (247, ''))

    def test_get_timeframe_with_two_parameters(self):
        "Make sure that timeframe() works correctly with two parameters"
        xmltree = etree.fromstring(
            '''<videoalpha
                    start_time="00:04:07"
                    end_time="13:04:39"
                >test</videoalpha>'''
        )
        output = self.xmodule.get_timeframe(xmltree)
        self.assertEqual(output, (247, 47079))


class VideoAlphaDescriptorTest(unittest.TestCase):
    """Test for VideoAlphaDescriptor"""

    def setUp(self):
        system = get_test_system()
        self.descriptor = VideoAlphaDescriptor(
            runtime=system,
            model_data={})

    def test_get_context(self):
        """"test get_context"""
        correct_tabs = [
            {
                'name': "XML",
                'template': "videoalpha/codemirror-edit.html",
                'css': {'scss': [resource_string(__name__,
                        '../css/tabs/codemirror.scss')]},
                'current': True,
            },
            {
                'name': "Settings",
                'template': "tabs/metadata-edit-tab.html"
            }
        ]
        rendered_context = self.descriptor.get_context()
        self.assertListEqual(rendered_context['tabs'], correct_tabs)
