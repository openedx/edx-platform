import json
from mock import Mock
import unittest

from xmodule.openendedchild import OpenEndedChild
from xmodule.modulestore import Location
from lxml import etree

from . import test_system

class OpenEndedChildTest(unittest.TestCase):
    location = Location(["i4x", "edX", "sa_test", "selfassessment",
                         "SampleQuestion"])

    metadata = json.dumps({'attempts': '10'})
    prompt = etree.XML("<prompt>This is a question prompt</prompt>")
    rubric = '''<rubric><rubric>
        <category>
        <description>Response Quality</description>
        <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
        </category>
         </rubric></rubric>'''
    max_score = 4

    static_data = {
            'max_attempts': 20,
            'prompt': prompt,
            'rubric': rubric,
            'max_score': max_score, 
            }
    definition = Mock()
    descriptor = Mock()


    def test_latest_answer_empty(self):
        openendedchild = OpenEndedChild(test_system, self.location, 
                self.definition, self.descriptor, self.static_data, self.metadata) 
        answer = openendedchild.latest_answer()
        self.assertEqual(answer, "")

    def test_latest_answer_nonempty(self):
        metadata = json.dumps({ 'attempts': 10,
                'history': [{'answer': "Two"}, {'answer': "Three"}]})
        openendedchild = OpenEndedChild(test_system, self.location, 
                self.definition, self.descriptor, self.static_data, metadata) 
        answer = openendedchild.latest_answer()
        self.assertEqual(answer, "Three")

    def test_latest_score_empty(self):
        openendedchild = OpenEndedChild(test_system, self.location, 
                self.definition, self.descriptor, self.static_data, self.metadata) 
        answer = openendedchild.latest_score()
        self.assertEqual(answer, None)


    def test_latest_score_nonempty(self):
        metadata = json.dumps({ 'attempts': 10,
                'history': [{'score': 3}, {'score': 2}]})
        openendedchild = OpenEndedChild(test_system, self.location, 
                self.definition, self.descriptor, self.static_data, metadata) 
        answer = openendedchild.latest_score()
        self.assertEqual(answer, 2)


    def test_new_history_entry(self):
        openendedchild = OpenEndedChild(test_system, self.location, 
                self.definition, self.descriptor, self.static_data, self.metadata) 
        new_answer = "New Answer"
        openendedchild.new_history_entry(new_answer)
        answer = openendedchild.latest_answer()
        self.assertEqual(answer, new_answer)

    #def test_record_latest_score(self):
