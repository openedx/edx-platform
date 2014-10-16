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
        # return anything except None to test LMS
        def test_real_user(useless):
            useless_user = Mock(email='fake@fake.com', id=useless)
            return useless_user

        # test to make sure that role is checked in LMS
        def test_user_role():
            return 'staff'

        self.system = get_test_system()
        self.system.get_real_user = test_real_user
        self.system.get_user_role = test_user_role
        self.system.anonymous_student_id = None

        self.mod = TextAnnotationModule(
            Mock(),
            self.system,
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

    def test_student_view(self):
        """
        Tests the function that passes in all the information in the context that will be used in templates/textannotation.html
        """
        context = self.mod.student_view({}).content
        for key in ['display_name', 'tag', 'source', 'instructions_html', 'content_html', 'annotation_storage', 'token', 'diacritic_marks', 'default_tab', 'annotation_mode', 'is_course_staff']:
            self.assertIn(key, context)
