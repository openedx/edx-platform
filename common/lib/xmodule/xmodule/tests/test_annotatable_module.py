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

    annotation_el = {
        'tag': 'annotation',
        'attrib': [
            'title',
            'body', # required
            'problem',
            'highlight'
        ]
    }

    def setUp(self):
        self.annotatable = AnnotatableModule(test_system, self.location, self.definition, self.descriptor, self.instance_state, self.shared_state)
