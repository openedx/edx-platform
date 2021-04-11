"""
Tests of symbolic math
"""

import re
import unittest

from lxml import etree

from . import formula


def stripXML(xml):
    xml = xml.replace('\n', '')
    xml = re.sub(r'\> +\<', '><', xml)
    return xml


class FormulaTest(unittest.TestCase):
    # for readability later
    mathml_start = '<math xmlns="http://www.w3.org/1998/Math/MathML"><mstyle displaystyle="true">'
    mathml_end = '</mstyle></math>'

    def setUp(self):
        super(FormulaTest, self).setUp()
        self.formulaInstance = formula('')

    def test_replace_mathvariants(self):
        expr = '''
<mstyle mathvariant="script">
  <mi>N</mi>
</mstyle>'''

        expected = '<mi>scriptN</mi>'

        # wrap
        expr = stripXML(self.mathml_start + expr + self.mathml_end)
        expected = stripXML(self.mathml_start + expected + self.mathml_end)

        # process the expression
        xml = etree.fromstring(expr)
        xml = self.formulaInstance.preprocess_pmathml(xml)
        test = etree.tostring(xml)

        # success?
        self.assertEqual(test.decode('utf-8'), expected)

    def test_fix_simple_superscripts(self):
        expr = '''
<msup>
  <mi>a</mi>
  <mrow>
    <mo>&#x200B;</mo>
    <mi>b</mi>
  </mrow>
</msup>'''

        expected = '<mi>a__b</mi>'

        # wrap
        expr = stripXML(self.mathml_start + expr + self.mathml_end)
        expected = stripXML(self.mathml_start + expected + self.mathml_end)

        # process the expression
        xml = etree.fromstring(expr)
        xml = self.formulaInstance.preprocess_pmathml(xml)
        test = etree.tostring(xml)

        # success?
        self.assertEqual(test.decode('utf-8'), expected)

    def test_fix_complex_superscripts(self):
        expr = '''
<msubsup>
  <mi>a</mi>
  <mi>b</mi>
  <mrow>
    <mo>&#x200B;</mo>
    <mi>c</mi>
  </mrow>
</msubsup>'''

        expected = '<mi>a_b__c</mi>'

        # wrap
        expr = stripXML(self.mathml_start + expr + self.mathml_end)
        expected = stripXML(self.mathml_start + expected + self.mathml_end)

        # process the expression
        xml = etree.fromstring(expr)
        xml = self.formulaInstance.preprocess_pmathml(xml)
        test = etree.tostring(xml)

        # success?
        self.assertEqual(test.decode('utf-8'), expected)

    def test_fix_msubsup(self):
        expr = '''
<msubsup>
  <mi>a</mi>
  <mi>b</mi>
  <mi>c</mi>
</msubsup>'''

        expected = '<msup><mi>a_b</mi><mi>c</mi></msup>'  # which is (a_b)^c

        # wrap
        expr = stripXML(self.mathml_start + expr + self.mathml_end)
        expected = stripXML(self.mathml_start + expected + self.mathml_end)

        # process the expression
        xml = etree.fromstring(expr)
        xml = self.formulaInstance.preprocess_pmathml(xml)
        test = etree.tostring(xml)

        # success?
        self.assertEqual(test.decode('utf-8'), expected)
