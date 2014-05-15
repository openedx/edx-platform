# -*- coding: utf-8 -*-
"Test for Annotation Xmodule functional logic."

import unittest
from mock import Mock
from lxml import etree

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.videoannotation_module import VideoAnnotationModule

from . import get_test_system


class VideoAnnotationModuleTestCase(unittest.TestCase):
    ''' Video Annotation Module Test Case '''
    sample_xml = '''
        <annotatable>
            <instructions><p>Video Test Instructions.</p></instructions>
        </annotatable>
    '''
    sample_sourceurl = "http://video-js.zencoder.com/oceans-clip.mp4"
    sample_youtubeurl = "http://www.youtube.com/watch?v=yxLIu-scR9Y"

    def setUp(self):
        """
        Makes sure that the Video Annotation Module is created.
        """
        self.mod = VideoAnnotationModule(
            Mock(),
            get_test_system(),
            DictFieldData({'data': self.sample_xml, 'sourceUrl': self.sample_sourceurl}),
            ScopeIds(None, None, None, None)
        )

    def test_annotation_class_attr_default(self):
        """
        Makes sure that it can detect annotation values in text-form if user
        decides to add text to the area below video, video functionality is completely
        found in javascript.
        """
        xml = '<annotation title="x" body="y" problem="0">test</annotation>'
        element = etree.fromstring(xml)

        expected_attr = {'class': {'value': 'annotatable-span highlight'}}
        actual_attr = self.mod._get_annotation_class_attr(element)  # pylint: disable=W0212

        self.assertIsInstance(actual_attr, dict)
        self.assertDictEqual(expected_attr, actual_attr)

    def test_annotation_class_attr_with_valid_highlight(self):
        """
        Same as above but more specific to an area that is highlightable in the appropriate
        color designated.
        """
        xml = '<annotation title="x" body="y" problem="0" highlight="{highlight}">test</annotation>'

        for color in self.mod.highlight_colors:
            element = etree.fromstring(xml.format(highlight=color))
            value = 'annotatable-span highlight highlight-{highlight}'.format(highlight=color)

            expected_attr = {'class': {
                'value': value,
                '_delete': 'highlight'}
            }
            actual_attr = self.mod._get_annotation_class_attr(element)  # pylint: disable=W0212

            self.assertIsInstance(actual_attr, dict)
            self.assertDictEqual(expected_attr, actual_attr)

    def test_annotation_class_attr_with_invalid_highlight(self):
        """
        Same as above, but checked with invalid colors.
        """
        xml = '<annotation title="x" body="y" problem="0" highlight="{highlight}">test</annotation>'

        for invalid_color in ['rainbow', 'blink', 'invisible', '', None]:
            element = etree.fromstring(xml.format(highlight=invalid_color))
            expected_attr = {'class': {
                'value': 'annotatable-span highlight',
                '_delete': 'highlight'}
            }
            actual_attr = self.mod._get_annotation_class_attr(element)  # pylint: disable=W0212

            self.assertIsInstance(actual_attr, dict)
            self.assertDictEqual(expected_attr, actual_attr)

    def test_annotation_data_attr(self):
        """
        Test that each highlight contains the data information from the annotation itself.
        """
        element = etree.fromstring('<annotation title="bar" body="foo" problem="0">test</annotation>')

        expected_attr = {
            'data-comment-body': {'value': 'foo', '_delete': 'body'},
            'data-comment-title': {'value': 'bar', '_delete': 'title'},
            'data-problem-id': {'value': '0', '_delete': 'problem'}
        }

        actual_attr = self.mod._get_annotation_data_attr(element)  # pylint: disable=W0212

        self.assertIsInstance(actual_attr, dict)
        self.assertDictEqual(expected_attr, actual_attr)

    def test_render_annotation(self):
        """
        Tests to make sure that the spans designating annotations acutally visually render as annotations.
        """
        expected_html = '<span class="annotatable-span highlight highlight-yellow" data-comment-title="x" data-comment-body="y" data-problem-id="0">z</span>'
        expected_el = etree.fromstring(expected_html)

        actual_el = etree.fromstring('<annotation title="x" body="y" problem="0" highlight="yellow">z</annotation>')
        self.mod._render_annotation(actual_el)  # pylint: disable=W0212

        self.assertEqual(expected_el.tag, actual_el.tag)
        self.assertEqual(expected_el.text, actual_el.text)
        self.assertDictEqual(dict(expected_el.attrib), dict(actual_el.attrib))

    def test_render_content(self):
        """
        Like above, but using the entire text, it makes sure that display_name is removed and that there is only one
        div encompassing the annotatable area.
        """
        content = self.mod._render_content()  # pylint: disable=W0212
        element = etree.fromstring(content)
        self.assertIsNotNone(element)
        self.assertEqual('div', element.tag, 'root tag is a div')
        self.assertFalse('display_name' in element.attrib, "Display Name should have been deleted from Content")

    def test_extract_instructions(self):
        """
        This test ensures that if an instruction exists it is pulled and
        formatted from the <instructions> tags. Otherwise, it should return nothing.
        """
        xmltree = etree.fromstring(self.sample_xml)

        expected_xml = u"<div><p>Video Test Instructions.</p></div>"
        actual_xml = self.mod._extract_instructions(xmltree)  # pylint: disable=W0212
        self.assertIsNotNone(actual_xml)
        self.assertEqual(expected_xml.strip(), actual_xml.strip())

        xmltree = etree.fromstring('<annotatable>foo</annotatable>')
        actual = self.mod._extract_instructions(xmltree)  # pylint: disable=W0212
        self.assertIsNone(actual)

    def test_get_extension(self):
        """
        Tests the function that returns the appropriate extension depending on whether it is
        a video from youtube, or one uploaded to the EdX server.
        """
        expectedyoutube = 'video/youtube'
        expectednotyoutube = 'video/mp4'
        result1 = self.mod._get_extension(self.sample_sourceurl)  # pylint: disable=W0212
        result2 = self.mod._get_extension(self.sample_youtubeurl)  # pylint: disable=W0212
        self.assertEqual(expectedyoutube, result2)
        self.assertEqual(expectednotyoutube, result1)

    def test_get_html(self):
        """
        Tests to make sure variables passed in truly exist within the html once it is all rendered.
        """
        context = self.mod.get_html()
        for key in ['display_name', 'content_html', 'instructions_html', 'sourceUrl', 'typeSource', 'poster', 'alert', 'annotation_storage']:
            self.assertIn(key, context)
