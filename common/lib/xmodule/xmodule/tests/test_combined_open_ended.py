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

    def setUp(self):
        self.openendedchild = OpenEndedChild(test_system, self.location, 
                self.definition, self.descriptor, self.static_data, self.metadata) 
 

    def test_latest_answer_empty(self):
        answer = self.openendedchild.latest_answer()
        self.assertEqual(answer, "")


    def test_latest_score_empty(self):
        answer = self.openendedchild.latest_score()
        self.assertEqual(answer, None)


    def test_latest_post_assessment_empty(self):
        answer = self.openendedchild.latest_post_assessment(test_system)
        self.assertEqual(answer, "")


    def test_new_history_entry(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)
        answer = self.openendedchild.latest_answer()
        self.assertEqual(answer, new_answer)

        new_answer = "Newer Answer"
        self.openendedchild.new_history_entry(new_answer)
        answer = self.openendedchild.latest_answer()
        self.assertEqual(new_answer, answer)

    def test_record_latest_score(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)
        new_score = 3
        self.openendedchild.record_latest_score(new_score)
        score = self.openendedchild.latest_score()
        self.assertEqual(score, 3)

        new_score = 4
        self.openendedchild.new_history_entry(new_answer)
        self.openendedchild.record_latest_score(new_score)
        score = self.openendedchild.latest_score()
        self.assertEqual(score, 4)


    def test_record_latest_post_assessment(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)

        post_assessment = "Post assessment"
        self.openendedchild.record_latest_post_assessment(post_assessment)
        self.assertEqual(post_assessment,
                self.openendedchild.latest_post_assessment(test_system))

    def test_get_score(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)

        score = self.openendedchild.get_score()
        self.assertEqual(score['score'], 0)
        self.assertEqual(score['total'], self.static_data['max_score'])

        new_score = 4
        self.openendedchild.new_history_entry(new_answer)
        self.openendedchild.record_latest_score(new_score)
        score = self.openendedchild.get_score()
        self.assertEqual(score['score'], new_score)
        self.assertEqual(score['total'], self.static_data['max_score'])

        
    def test_reset(self):
        self.openendedchild.reset(test_system)
        state = json.loads(self.openendedchild.get_instance_state())
        self.assertEqual(state['state'], OpenEndedChild.INITIAL)
        

    def test_is_last_response_correct(self):
        new_answer = "New Answer"
        self.openendedchild.new_history_entry(new_answer)
        self.openendedchild.record_latest_score(self.static_data['max_score'])
        self.assertEqual(self.openendedchild.is_last_response_correct(),
                'correct')

        self.openendedchild.new_history_entry(new_answer)
        self.openendedchild.record_latest_score(0)
        self.assertEqual(self.openendedchild.is_last_response_correct(),
                'incorrect')



