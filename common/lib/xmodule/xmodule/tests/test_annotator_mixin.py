"""
This test will run for annotator_mixin.py
"""

import unittest
from lxml import etree

from xmodule.annotator_mixin import get_instructions, get_extension, html_to_text


class HelperFunctionTest(unittest.TestCase):
    """
    Tests to ensure that the following helper functions work for the annotation tool
    """
    sample_xml = '''
        <annotatable>
            <instructions><p>Helper Test Instructions.</p></instructions>
        </annotatable>
    '''
    sample_sourceurl = "http://video-js.zencoder.com/oceans-clip.mp4"
    sample_youtubeurl = "http://www.youtube.com/watch?v=yxLIu-scR9Y"
    sample_html = '<p><b>Testing here</b> and not bolded here</p>'

    def test_get_instructions(self):
        """
        Function takes in an input of a specific xml string with surrounding instructions
        tags and returns a valid html string.
        """
        xmltree = etree.fromstring(self.sample_xml)

        expected_xml = u"<div><p>Helper Test Instructions.</p></div>"
        actual_xml = get_instructions(xmltree)
        self.assertIsNotNone(actual_xml)
        self.assertEqual(expected_xml.strip(), actual_xml.strip())

        xmltree = etree.fromstring('<annotatable>foo</annotatable>')
        actual = get_instructions(xmltree)
        self.assertIsNone(actual)

    def test_get_extension(self):
        """
        Tests whether given a url if the video will return a youtube source or extension
        """
        expectedyoutube = 'video/youtube'
        expectednotyoutube = 'video/mp4'
        result1 = get_extension(self.sample_sourceurl)
        result2 = get_extension(self.sample_youtubeurl)
        self.assertEqual(expectedyoutube, result2)
        self.assertEqual(expectednotyoutube, result1)

    def test_html_to_text(self):
        expectedtext = "Testing here and not bolded here"
        result = html_to_text(self.sample_html)
        self.assertEqual(expectedtext, result)
