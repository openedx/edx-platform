import unittest
from lxml import etree
import os
import textwrap

import mock

from .response_xml_factory import StringResponseXMLFactory, CustomResponseXMLFactory
from . import test_system, new_loncapa_problem

import ipdb

class CapaShuffleTest(unittest.TestCase):

    def setUp(self):
        super(CapaShuffleTest, self).setUp()
        self.system = test_system()

    def test_shuffle_4_choices(self):
        xml_str = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" shuffle="true">
                <choice correct="false">Apple</choice>
                <choice correct="false">Banana</choice>
                <choice correct="false">Chocolate</choice>
                <choice correct ="true">Donut</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 0
        # shuffling 4 things with seed of 0 yields: B A C D
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'Banana'.*'Apple'.*'Chocolate'.*'Donut'.*\].*</div>")

    def test_shuffle_1_choice(self):
        xml_str = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" shuffle="true">
                <choice correct="true">Apple</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 0
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'Apple'.*\].*</div>")

    def test_shuffle_6_choices(self):
        xml_str = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" shuffle="true">
                <choice correct="false">Apple</choice>
                <choice correct="false">Banana</choice>
                <choice correct="false">Chocolate</choice>
                <choice correct ="true">Zonut</choice>
                <choice correct ="false">Eggplant</choice>
                <choice correct ="false">Filet Mignon</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 0
        # shuffling 6 things with seed of 0 yields: C E A B D F
        # Donut -> Zonut to show that there is not some hidden alphabetic ordering going on
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'Chocolate'.*'Eggplant'.*'Apple'.*'Banana'.*'Zonut'.*'Filet Mignon'.*\].*</div>")

    def test_shuffle_false(self):
        xml_str = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" shuffle="false">
                <choice correct="false">Apple</choice>
                <choice correct="false">Banana</choice>
                <choice correct="false">Chocolate</choice>
                <choice correct ="true">Donut</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 0
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'Apple'.*'Banana'.*'Chocolate'.*'Donut'.*\].*</div>")

    def test_shuffle_fixed_head_end(self):
        xml_str = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" shuffle="true">
                <choice correct="false" fixed="true">Alpha</choice>
                <choice correct="false" fixed="true">Beta</choice>
                <choice correct="false">A</choice>
                <choice correct="false">B</choice>
                <choice correct="false">C</choice>
                <choice correct ="true">D</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 0
        the_html = problem.get_html()
        # Alpha Beta held back from shuffle (head end)
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'Alpha'.*'Beta'.*'B'.*'A'.*'C'.*'D'.*\].*</div>")

    def test_shuffle_fixed_tail_end(self):
        xml_str = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" shuffle="true">
                <choice correct="false">A</choice>
                <choice correct="false">B</choice>
                <choice correct="false">C</choice>
                <choice correct ="true">D</choice>
                <choice correct="false" fixed="true">Alpha</choice>
                <choice correct="false" fixed="true">Beta</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 0
        the_html = problem.get_html()
        #print the_html
        # Alpha Beta held back from shuffle (tail end)
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'B'.*'A'.*'C'.*'D'.*'Alpha'.*'Beta'.*\].*</div>")


    def test_shuffle_fixed_both_ends(self):
        xml_str = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" shuffle="true">
                <choice correct="false" fixed="true">Alpha</choice>
                <choice correct="false" fixed="true">Beta</choice>
                <choice correct="false">A</choice>
                <choice correct="false">B</choice>
                <choice correct="false">C</choice>
                <choice correct ="true">D</choice>
                <choice correct="false" fixed="true">Psi</choice>
                <choice correct="false" fixed="true">Omega</choice>

              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 0
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'Alpha'.*'Beta'.*'B'.*'A'.*'C'.*'D'.*'Psi'.*'Omega'.*\].*</div>")

    def test_shuffle_fixed_both_ends_thin(self):
        xml_str = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" shuffle="true">
                <choice correct="false" fixed="true">Alpha</choice>
                <choice correct="false">A</choice>
                <choice correct="true" fixed="true">Omega</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 0
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'Alpha'.*'A'.*'Omega'.*\].*</div>")

    def test_shuffle_fixed_all(self):
        xml_str = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" shuffle="true">
                <choice correct="false" fixed="true">A</choice>
                <choice correct="false" fixed="true">B</choice>
                <choice correct="true" fixed="true">C</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        problem = new_loncapa_problem(xml_str)
        problem.seed = 0
        the_html = problem.get_html()
        self.assertRegexpMatches(the_html, r"<div>.*\[.*'A'.*'B'.*'C'.*\].*</div>")

