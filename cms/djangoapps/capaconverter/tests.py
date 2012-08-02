#!/usr/bin/env python

from django.utils import unittest
import logging
import os.path
from __init__ import CapaXMLConverter
import json
import sys
from lxml import etree


class CapaXMLConverterTestCase(unittest.TestCase):
    def setUp(self):
        self.converter = CapaXMLConverter()
        self.converter.logger.setLevel(logging.DEBUG)
        self.problems_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "problems")
        logging.info("Testing problems from folder %s" % self.problems_folder)
        self.problem_files = map(lambda filename: os.path.join(self.problems_folder, filename),
                        filter(lambda filename: filename.endswith(".xml"), 
                        os.listdir(self.problems_folder)))
        logging.info("Found %d lon-CAPA XML files. " % len(self.problem_files))

    def test_center(self):
        xml = '<center><img src="/aa" /></center>'
        elements = self.converter.picky_center_element_format(etree.fromstring(xml))
        self.assertEqual(elements, [{'url': '/aa', '_tag_': 'img', 'type': 'image'}])

        xml = '<center><img src="/aa" />title</center>'
        elements = self.converter.picky_center_element_format(etree.fromstring(xml))
        self.assertEqual(elements, [{'url': '/aa', '_tag_': 'img', 'type': 'image', 'title': 'title'}])

        xml = '<center><img src="/aa" />title<input /></center>'
        elements = self.converter.picky_center_element_format(etree.fromstring(xml))
        self.assertEqual(elements, None)

    def test_iterator(self):
        xml = """<text>In this problem we will investigate a fun idea called "duality."
<br />
Consider the series circuit in the diagram shown.
<center>
<img src="/static/images/circuits/duality.gif" />
</center>
We are given device parameters \(V=$V\)V, \(R_1=$R1\Omega\), and \(R_2=$R2\Omega\).
All of the unknown voltages and currents are labeled in associated reference
directions.  Solve this circuit for the unknowns and enter them into
the boxes given.
<br />
The value (in Volts) of \(v_1\) is: </text>"""
        elements = list(self.converter.iterate_element(etree.fromstring(xml)))
        self.assertEqual(7, len(elements))

    def test_xmls(self):
        for filepath in self.problem_files:
            try:
                out = self.converter.convert_xml_file(filepath)
            except:
                print "Failed to convert file %s" % filepath
                raise
            f = open(filepath.replace(".xml", ".json"), "w")
            json.dump(out, f, indent=2)
            f.close()


if __name__ == '__main__':
    unittest.main()