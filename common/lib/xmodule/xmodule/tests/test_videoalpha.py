# -*- coding: utf-8 -*-
"""Test for Video Alpha Xmodule functional logic.
These tests data readed from  xml, not from mongo.

we have a ModuleStoreTestCase class defined in
common/lib/xmodule/xmodule/modulestore/tests/django_utils.py. You can
search for usages of this in the cms and lms tests for examples. You use
this so that it will do things like point the modulestore setting to mongo,
flush the contentstore before and after, load the templates, etc.
You can then use the CourseFactory and XModuleItemFactory as defined
in common/lib/xmodule/xmodule/modulestore/tests/factories.py to create
the course, section, subsection, unit, etc.
"""

from xmodule.videoalpha_module import VideoAlphaDescriptor
from . import LogicTest, etree


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
