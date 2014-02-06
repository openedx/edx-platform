# -*- coding: utf-8 -*-
"Test for Annotation Xmodule functional logic."

import unittest
from mock import Mock
from lxml import etree

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.textannotation_module import VideoAnnotationModule
from xmodule.modulestore import Location

from . import get_test_system

class VideoAnnotationModuleTestCase(unittest.TestCase):
    sample_xml = '''
        <annotatable>
            <instructions><p>Video Test Instructions.</p></instructions>
        </annotatable>
    '''
    sample_sourceURL = "http://video-js.zencoder.com/oceans-clip.mp4"
    sample_youtubeURL = "http://www.youtube.com/watch?v=yxLIu-scR9Y"
    
    def setUp(self):
        self.mod = VideoAnnotationModule(
            Mock(),
            get_test_system(),
            DictFieldData({'data':self.sample_xml, 'sourceUrl':sample_sourceURL}),
            ScopeIds(None, None, None, None)
        )

    def test_extract_instructions(self):
        xmltree = etree.fromstring(self.sample_xml)

        expected_xml = u"<div><p>Video Test Instructions.</p></div>"
        actual_xml = self.mod._extract_instructions(xmltree)  # pylint: disable=W0212

        self.assertIsNotNone(actual_xml)
        self.assertEqual(expected_xml.strip(), actual_xml.strip())

        xmltree = etree.fromstring('<annotatable>foo</annotatable>')
        actual = self.mod._extract_instructions(xmltree)
        self.assertIsNone(actual)
    
    def test_get_extension(self):
        expectedYoutube = 'video/youtube'
        expectedNotYoutube = 'video/mp4'
        result1 = self.mod._get_extension(sample_sourceURL)
        result2 = self.mod._get_extension(sample_youtubeURL)
        self.assertEqual(expectedYoutube, result2)
        self.assertEqual(expectedNotYoutube, result1)
    
    def test_get_html(self):
        """
        Tests to make sure variables passed in truly exist within the html once it is all rendered.
        """
        context = self.mod.get_html()  # pylint: disable=W0212
        for key in ['display_name', 'instructions_html', 'sourceUrl', 'typeSource', 'poster', 'annotation_storage']:
            self.assertIn(key, context)
