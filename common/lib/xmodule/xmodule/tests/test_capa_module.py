import json
from mock import Mock
import unittest

from xmodule.capa_module import CapaModule
from xmodule.modulestore import Location
from lxml import etree

from . import test_system

class CapaFactory(object):
    """
    A helper class to create problem modules with various parameters for testing.
    """

    sample_problem_xml = """<?xml version="1.0"?>
<problem>
  <text>
    <p>What is pi, to two decimal placs?</p>
  </text>
<numericalresponse answer="3.14">
<textline math="1" size="30"/>
</numericalresponse>
</problem>
"""

    num = 0
    @staticmethod
    def next_num():
        CapaFactory.num += 1
        return CapaFactory.num

    @staticmethod
    def create():
        definition = {'data': CapaFactory.sample_problem_xml,}
        location = Location(["i4x", "edX", "capa_test", "problem",
                             "SampleProblem{0}".format(CapaFactory.next_num())])
        metadata = {}
        descriptor = Mock(weight="1")
        instance_state = None

        module = CapaModule(test_system, location,
                            definition, descriptor,
                                      instance_state, None, metadata=metadata)

        return module



class CapaModuleTest(unittest.TestCase):

    def test_import(self):
        module = CapaFactory.create()
        self.assertEqual(module.get_score()['score'], 0)

        other_module = CapaFactory.create()
        self.assertEqual(module.get_score()['score'], 0)
        self.assertNotEqual(module.url_name, other_module.url_name,
                            "Factory should be creating unique names for each problem")

