from lxml import etree
import unittest
import xml.sax.saxutils as saxutils

from capa.tests.helpers import test_capa_system
from capa import customrender

# just a handy shortcut
lookup_tag = customrender.registry.get_class_for_tag


def extract_context(xml):
    """
    Given an xml element corresponding to the output of test_capa_system.render_template, get back the
    original context
    """
    return eval(xml.text)


def quote_attr(s):
    return saxutils.quoteattr(s)[1:-1]  # don't want the outer quotes


class HelperTest(unittest.TestCase):
    '''
    Make sure that our helper function works!
    '''
    def check(self, d):
        xml = etree.XML(test_capa_system().render_template('blah', d))
        self.assertEqual(d, extract_context(xml))

    def test_extract_context(self):
        self.check({})
        self.check({1, 2})
        self.check({'id', 'an id'})
        self.check({'with"quote', 'also"quote'})


class SolutionRenderTest(unittest.TestCase):
    '''
    Make sure solutions render properly.
    '''

    def test_rendering(self):
        solution = 'To compute unicorns, count them.'
        xml_str = """<solution id="solution_12">{s}</solution>""".format(s=solution)
        element = etree.fromstring(xml_str)

        renderer = lookup_tag('solution')(test_capa_system(), element)

        self.assertEqual(renderer.id, 'solution_12')

        # Our test_capa_system "renders" templates to a div with the repr of the context.
        xml = renderer.get_html()
        context = extract_context(xml)
        self.assertEqual(context, {'id': 'solution_12'})


class MathRenderTest(unittest.TestCase):
    '''
    Make sure math renders properly.
    '''

    def check_parse(self, latex_in, mathjax_out):
        xml_str = """<math>{tex}</math>""".format(tex=latex_in)
        element = etree.fromstring(xml_str)

        renderer = lookup_tag('math')(test_capa_system(), element)

        self.assertEqual(renderer.mathstr, mathjax_out)

    def test_parsing(self):
        self.check_parse('$abc$', '[mathjaxinline]abc[/mathjaxinline]')
        self.check_parse('$abc', '$abc')
        self.check_parse(r'$\displaystyle 2+2$', '[mathjax] 2+2[/mathjax]')

    # NOTE: not testing get_html yet because I don't understand why it's doing what it's doing.
