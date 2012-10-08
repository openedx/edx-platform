"""
Tests of input types (and actually responsetypes too)
"""


from datetime import datetime
import json
from nose.plugins.skip import SkipTest
import os
import unittest

from . import test_system
from capa import inputtypes

from lxml import etree

class OptionInputTest(unittest.TestCase):
    '''
    Make sure option inputs work
    '''
    def test_rendering(self):
        xml = """<optioninput options="('Up','Down')" id="sky_input" correct="Up"/>"""
        element = etree.fromstring(xml)

        value = 'Down'
        status = 'incorrect'
        rendered_element = inputtypes.optioninput(element, value, status, test_system.render_template)
        rendered_str = etree.tostring(rendered_element)
        print rendered_str
        self.assertTrue(False)



        # TODO: split each inputtype into a get_render_context function and a
        # template property, and have the rendering done in one place.  (and be
        # able to test the logic without dealing with xml at least on the output
        # end)
