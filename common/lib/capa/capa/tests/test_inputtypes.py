"""
Tests of input types (and actually responsetypes too)
"""

from datetime import datetime
import json
from mock import Mock
from nose.plugins.skip import SkipTest
import os
import unittest

from . import test_system
from capa import inputtypes

from lxml import etree

def tst_render_template(template, context):
    """
    A test version of render to template.  Renders to the repr of the context, completely ignoring the template name.
    """
    return repr(context)


system = Mock(render_template=tst_render_template)

class OptionInputTest(unittest.TestCase):
    '''
    Make sure option inputs work
    '''

    def test_rendering(self):
        xml_str = """<optioninput options="('Up','Down')" id="sky_input" correct="Up"/>"""
        element = etree.fromstring(xml_str)

        state = {'value': 'Down',
                 'id': 'sky_input',
                 'status': 'answered'}
        option_input = inputtypes.OptionInput(system, element, state)

        context = option_input._get_render_context()

        expected = {'value': 'Down',
                    'options': [('Up', 'Up'), ('Down', 'Down')],
                    'state': 'answered',
                    'msg': '',
                    'inline': '',
                    'id': 'sky_input'}

        self.assertEqual(context, expected)

class ChoiceGroupTest(unittest.TestCase):
    '''
    Test choice groups.
    '''
    def test_mult_choice(self):
        xml_str = """
  <choicegroup>
    <choice correct="false" name="foil1">
      <startouttext />This is foil One.<endouttext />
    </choice>
    <choice correct="false" name="foil2">
      <startouttext />This is foil Two.<endouttext />
    </choice>
    <choice correct="true" name="foil3">
      <startouttext />This is foil Three.<endouttext />
    </choice>
    <choice correct="false" name="foil4">
      <startouttext />This is foil Four.<endouttext />
    </choice>
    <choice correct="false" name="foil5">
      <startouttext />This is foil Five.<endouttext />
    </choice>
  </choicegroup>
        """
        element = etree.fromstring(xml_str)

        state = {'value': 'Down',
                 'id': 'sky_input',
                 'status': 'answered'}
        option_input = inputtypes.OptionInput(system, element, state)

        context = option_input._get_render_context()

        expected = {'value': 'Down',
                    'options': [('Up', 'Up'), ('Down', 'Down')],
                    'state': 'answered',
                    'msg': '',
                    'inline': '',
                    'id': 'sky_input'}

        self.assertEqual(context, expected)

