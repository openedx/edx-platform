# -*- coding: utf-8 -*-
"Test for Annotation Xmodule functional logic."

import unittest
from mock import Mock
from lxml import etree

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.textannotation_module import TextAnnotationModule

from . import get_test_system

class TextAnnotationModuleTestCase(unittest.TestCase):
    ''' text Annotation Module Test Case '''
    sample_xml = '''
        <annotatable>
            <instructions><p>Test Instructions.</p></instructions>
            <p>
                One Fish. Two Fish.
                Red Fish. Blue Fish.

                Oh the places you'll go!
            </p>
        </annotatable>
    '''
    def setUp(self):
        """
            Makes sure that the Module is declared and mocked with the sample xml above.
        """
        self.mod = TextAnnotationModule(
            Mock(),
            get_test_system(),
            DictFieldData({'data': self.sample_xml}),
            ScopeIds(None, None, None, None)
        )

    def test_extract_instructions(self):
        """
        Tests to make sure that the instructions are correctly pulled from the sample xml above.
        It also makes sure that if no instructions exist, that it does in fact return nothing.
        """
        xmltree = etree.fromstring(self.sample_xml)

        expected_xml = u"<div><p>Test Instructions.</p></div>"
        actual_xml = self.mod._extract_instructions(xmltree)  # pylint: disable=W0212
        self.assertIsNotNone(actual_xml)
        self.assertEqual(expected_xml.strip(), actual_xml.strip())

        xmltree = etree.fromstring('<annotatable>foo</annotatable>')
        actual = self.mod._extract_instructions(xmltree)  # pylint: disable=W0212
        self.assertIsNone(actual)

    def test_token(self):
        """
        Test for the token generator. This creates a random course and passes it through the token file which generates the
        token that will be passed in to the annotation_storage_url.
        """
        expected = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpc3N1ZWRBdCI6ICIyMDE0LTAxLTIzVDE5OjM1OjE3LjUyMjEwNC01OjAwIiwgImNvbnN1bWVyS2V5IjogInh4eHh4eHh4LXh4eHgteHh4eC14eHh4LXh4eHh4eHh4eHh4eCIsICJ1c2VySWQiOiAidXNlcm5hbWUiLCAidHRsIjogODY0MDB9.OjWz9mzqJnYuzX-f3uCBllqJUa8PVWJjcDy_McfxLvc"
        response = self.mod.token("username")
        self.assertEqual(expected.split('.')[0], response.split('.')[0])

    def test_get_html(self):
        """
        Tests the function that passes in all the information in the context that will be used in templates/textannotation.html
        """
        context = self.mod.get_html()
        for key in ['display_name', 'tag', 'source', 'instructions_html', 'content_html', 'annotation_storage', 'token']:
            self.assertIn(key, context)
