from mock import Mock, patch
import unittest
import copy

import xmodule
from xmodule.crowdsource_hinter import CrowdsourceHinterModule
from xmodule.modulestore import Location

from django.http import QueryDict

from . import test_system

import json

class CHModuleFactory(object):
    '''
    Helps us make a CrowdsourceHinterModule with the specified internal
    state.
    '''

    sample_problem_xml = '''
    <?xml version="1.0"?>
    <crowdsource_hinter>
        <problem display_name="Numerical Input" markdown="A numerical input problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.&#10;&#10;The answer is correct if it is within a specified numerical tolerance of the expected answer.&#10;&#10;Enter the number of fingers on a human hand:&#10;= 5&#10;&#10;[explanation]&#10;If you look at your hand, you can count that you have five fingers. [explanation] " rerandomize="never" showanswer="finished">
          <p>A numerical input problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.</p>
          <p>The answer is correct if it is within a specified numerical tolerance of the expected answer.</p>
          <p>Enter the number of fingers on a human hand:</p>
          <numericalresponse answer="5">
            <textline/>
          </numericalresponse>
          <solution>
            <div class="detailed-solution">
              <p>Explanation</p>
              <p>If you look at your hand, you can count that you have five fingers. </p>
            </div>
          </solution>
        </problem>
    </crowdsource_hinter>
    '''

    num = 0

    @staticmethod
    def next_num():
        CHModuleFactory.num += 1
        return CHModuleFactory.num

    @staticmethod
    def create(hints=None,
               previous_answers=None,
               user_voted=None,
               moderate=None,
               mod_queue=None):

        location = Location(["i4x", "edX", "capa_test", "problem",
                             "SampleProblem{0}".format(CHModuleFactory.next_num())])
        model_data = {'data': CHModuleFactory.sample_problem_xml}

        if hints != None:
            model_data['hints'] = hints
        else:
            model_data['hints'] = {
                '24.0': {'0': ['Best hint', 40],
                          '3': ['Another hint', 30],
                          '4': ['A third hint', 20],
                          '6': ['A less popular hint', 3]},
                '25.0': {'1': ['Really popular hint', 100]}
            }

        if mod_queue != None:
            model_data['mod_queue'] = mod_queue
        else:
            model_data['mod_queue'] = {
                '24.0': {'2': ['A non-approved hint']},
                '26.0': {'5': ['Another non-approved hint']}
            }

        if previous_answers != None:
            model_data['previous_answers'] = previous_answers
        else:
            model_data['previous_answers'] = [
                ['24.0', [0, 3, 4]],
                ['29.0', [None, None, None]]
            ]

        if user_voted != None:
            model_data['user_voted'] = user_voted

        if moderate != None:
            model_data['moderate'] = moderate
        
        descriptor = Mock(weight="1")
        system = test_system()
        system.render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CrowdsourceHinterModule(system, descriptor, model_data)

        return module

class CrowdsourceHinterTest(unittest.TestCase):
    '''
    In the below tests, '24.0' represents a wrong answer, and '42.5' represents
    a correct answer.
    '''

    def test_gethint_0hint(self):
        '''
        Someone asks for a hint, when there's no hint to give.
        - Output should be blank.
        - New entry should be added to previous_answers
        '''
        m = CHModuleFactory.create()
        json_in = {'problem_name': '26.0'}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue(json_out == ' ')
        self.assertTrue(['26.0', [None, None, None]] in m.previous_answers)

    def test_gethint_1hint(self):
        '''
        Someone asks for a hint, with exactly one hint in the database.
        Output should contain that hint.
        '''
        m = CHModuleFactory.create()
        json_in = {'problem_name': '25.0'}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue('Really popular hint' in json_out)


    def test_gethint_manyhints(self):
        '''
        Someone asks for a hint, with many matching hints in the database.
        - The top-rated hint should be returned.
        - Two other random hints should be returned.
        Currently, the best hint could be returned twice - need to fix this
        in implementation.
        '''
        m = CHModuleFactory.create()
        json_in = {'problem_name': '24.0'}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue('Best hint' in json_out)
        self.assertTrue(json_out.count('hint') == 3)


    def test_getfeedback_0wronganswers(self):
        '''
        Someone has gotten the problem correct on the first try.
        Output should be empty.
        '''
        m = CHModuleFactory.create(previous_answers=[])
        json_in = {'problem_name': '42.5'}
        json_out = json.loads(m.get_feedback(json_in))['contents']
        self.assertTrue(json_out == ' ')

    def test_getfeedback_1wronganswer_nohints(self):
        '''
        Someone has gotten the problem correct, with one previous wrong
        answer.  However, we don't actually have hints for this problem.
        There should be a dialog to submit a new hint.
        '''
        m = CHModuleFactory.create(previous_answers=[['26.0',[None, None, None]]])
        json_in = {'problem_name': '42.5'}
        json_out = json.loads(m.get_feedback(json_in))['contents']
        self.assertTrue('textarea' in json_out)
        self.assertTrue('Vote' not in json_out)


    def test_getfeedback_1wronganswer_withhints(self):
        '''
        Same as above, except the user did see hints.  There should be
        a voting dialog, with the correct choices, plus a hint submission
        dialog.
        '''
        m = CHModuleFactory.create(
            previous_answers=[
                ['24.0', [0, 3, None]]],
            )
        json_in = {'problem_name': '42.5'}
        json_out = json.loads(m.get_feedback(json_in))['contents']
        self.assertTrue('Best hint' in json_out)
        self.assertTrue('Another hint' in json_out)
        self.assertTrue('third hint' not in json_out)
        self.assertTrue('textarea' in json_out)


    def test_vote_nopermission(self):
        '''
        A user tries to vote for a hint, but he has already voted!
        Should not change any vote tallies.
        '''
        m = CHModuleFactory.create(user_voted=True)
        json_in = {'answer': 0, 'hint': 1}
        old_hints = copy.deepcopy(m.hints)
        json_out = json.loads(m.tally_vote(json_in))['contents']
        self.assertTrue(m.hints == old_hints)


    def test_vote_withpermission(self):
        '''
        A user votes for a hint.
        '''
        m = CHModuleFactory.create()
        json_in = {'answer': 0, 'hint': 3}
        json_out = json.loads(m.tally_vote(json_in))['contents'] 
        self.assertTrue(m.hints['24.0']['0'][1] == 40)
        self.assertTrue(m.hints['24.0']['3'][1] == 31)
        self.assertTrue(m.hints['24.0']['4'][1] == 20)


    def test_submithint_nopermission(self):
        '''
        A user tries to submit a hint, but he has already voted.
        '''
        m = CHModuleFactory.create(user_voted=True)
        json_in = {'answer': 1, 'hint': 'This is a new hint.'}
        m.submit_hint(json_in)
        self.assertTrue('29.0' not in m.hints)


    def test_submithint_withpermission_new(self):
        '''
        A user submits a hint to an answer for which no hints
        exist yet.
        '''
        m = CHModuleFactory.create()
        json_in = {'answer': 1, 'hint': 'This is a new hint.'}
        m.submit_hint(json_in)
        # Make a hint request.
        json_in = {'problem name': '29.0'}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue('This is a new hint.' in json_out)


    def test_submithint_withpermission_existing(self):
        '''
        A user submits a hint to an answer that has other hints
        already.
        '''
        m = CHModuleFactory.create(previous_answers = [['25.0', [1, None, None]]])
        json_in = {'answer': 0, 'hint': 'This is a new hint.'}
        m.submit_hint(json_in)
        # Make a hint request.
        json_in = {'problem name': '25.0'}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue('This is a new hint.' in json_out)


    def test_submithint_moderate(self):
        '''
        A user submits a hint, but moderation is on.  The hint should
        show up in the mod_queue, not the public-facing hints
        dict.
        '''
        m = CHModuleFactory.create(moderate='True')
        json_in = {'answer': 1, 'hint': 'This is a new hint.'}
        m.submit_hint(json_in)
        self.assertTrue('29.0' not in m.hints)
        self.assertTrue('29.0' in m.mod_queue)














