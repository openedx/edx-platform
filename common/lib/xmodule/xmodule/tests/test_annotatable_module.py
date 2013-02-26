"""Module annotatable tests"""

import unittest

from lxml import etree
from mock import Mock

from xmodule.annotatable_module import AnnotatableModule
from xmodule.modulestore import Location

from . import test_system

class AnnotatableModuleTestCase(unittest.TestCase):
    location = Location(["i4x", "edX", "toy", "annotatable", "guided_discussion"])
    sample_text = '''
        <annotatable display_name="Iliad">
            <instructions>Read the text.</instructions>
            <p>
                <annotation body="first">Sing</annotation>,
                <annotation title="goddess" body="second">O goddess</annotation>,
                <annotation title="anger" body="third" highlight="blue">the anger of Achilles son of Peleus</annotation>,
                that brought <i>countless</i> ills upon the Achaeans. Many a brave soul did it send
                hurrying down to Hades, and many a hero did it yield a prey to dogs and
                <div style="font-weight:bold"><annotation body="fourth" problem="4">vultures</annotation>, for so were the counsels
                of Jove fulfilled from the day on which the son of Atreus, king of men, and great
                Achilles, first fell out with one another.</div>
            </p>
            <annotation title="footnote" body="the end">The Iliad of Homer by Samuel Butler</annotation>
        </annotatable>
    '''
    definition = { 'data': sample_text }
    descriptor = Mock()
    instance_state = None
    shared_state = None

    def setUp(self):
        self.annotatable = AnnotatableModule(test_system, self.location, self.definition, self.descriptor, self.instance_state, self.shared_state)

    def test_annotation_data_attr(self):
        el = etree.fromstring('<annotation title="bar" body="foo" problem="0">test</annotation>')

        expected_attr = {
            'data-comment-body': {'value': 'foo', '_delete': 'body' },
            'data-comment-title': {'value': 'bar', '_delete': 'title'},
            'data-problem-id': {'value': '0', '_delete': 'problem'}
        }

        data_attr = self.annotatable._get_annotation_data_attr(0, el)
        self.assertTrue(type(data_attr) is dict)
        self.assertDictEqual(expected_attr, data_attr)