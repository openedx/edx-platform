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
    
    def test_annotation_class_attr_default(self):
        xml = '<annotation title="x" body="y" problem="0">test</annotation>'
        el = etree.fromstring(xml)

        expected_attr = { 'class': { 'value': 'annotatable-span highlight' } }
        actual_attr = self.mod._get_annotation_class_attr(0, el)

        self.assertIsInstance(actual_attr, dict)
        self.assertDictEqual(expected_attr, actual_attr)

    def test_annotation_class_attr_with_valid_highlight(self):
        xml = '<annotation title="x" body="y" problem="0" highlight="{highlight}">test</annotation>'

        for color in self.mod.highlight_colors:
            el = etree.fromstring(xml.format(highlight=color))
            value = 'annotatable-span highlight highlight-{highlight}'.format(highlight=color)

            expected_attr = { 'class': {
                'value': value,
                '_delete': 'highlight' }
            }
            actual_attr = self.mod._get_annotation_class_attr(0, el)

            self.assertIsInstance(actual_attr, dict)
            self.assertDictEqual(expected_attr, actual_attr)

    def test_annotation_class_attr_with_invalid_highlight(self):
        xml = '<annotation title="x" body="y" problem="0" highlight="{highlight}">test</annotation>'

        for invalid_color in ['rainbow', 'blink', 'invisible', '', None]:
            el = etree.fromstring(xml.format(highlight=invalid_color))
            expected_attr = { 'class': {
                'value': 'annotatable-span highlight',
                '_delete': 'highlight' }
            }
            actual_attr = self.mod._get_annotation_class_attr(0, el)

            self.assertIsInstance(actual_attr, dict)
            self.assertDictEqual(expected_attr, actual_attr)
    
    def test_annotation_data_attr(self):
        el = etree.fromstring('<annotation title="bar" body="foo" problem="0">test</annotation>')

        expected_attr = {
            'data-comment-body': {'value': 'foo', '_delete': 'body' },
            'data-comment-title': {'value': 'bar', '_delete': 'title'},
            'data-problem-id': {'value': '0', '_delete': 'problem'}
        }
        
        actual_attr = self.mod._get_annotation_data_attr(0, el)
        
        self.assertIsInstance(actual_attr, dict)
        self.assertDictEqual(expected_attr, actual_attr)
    
    def test_render_annotation(self):
        expected_html = '<span class="annotatable-span highlight highlight-yellow" data-comment-title="x" data-comment-body="y" data-problem-id="0">z</span>'
        expected_el = etree.fromstring(expected_html)

        actual_el = etree.fromstring('<annotation title="x" body="y" problem="0" highlight="yellow">z</annotation>')
        self.mod._render_annotation(0, actual_el)

        self.assertEqual(expected_el.tag, actual_el.tag)
        self.assertEqual(expected_el.text, actual_el.text)
        self.assertDictEqual(dict(expected_el.attrib), dict(actual_el.attrib))
    
    def test_render_content(self):
        content = self.mod._render_content()
        el = etree.fromstring(content)

        self.assertEqual('div', el.tag, 'root tag is a div')

        expected_num_annotations = 5
        actual_num_annotations = el.xpath('count(//span[contains(@class,"annotatable-span")])')
        self.assertEqual(expected_num_annotations, actual_num_annotations, 'check number of annotations')
    
    def test_extract_instructions(self):
        xmltree = etree.fromstring(self.sample_xml)

        expected_xml = u"<div>Read the text.</div>"
        actual_xml = self.mod._extract_instructions(xmltree)
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
        context = self.mod.get_html()
        for key in ['display_name', 'element_id', 'content_html', 'instructions_html', 'sourceUrl','typeSource','poster','alert','annotation_storage']:
            self.assertIn(key, context)