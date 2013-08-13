"""
Tests the crowdsourced hinter xmodule.
"""

from mock import Mock
import unittest
import copy

from xmodule.crowdsource_hinter import CrowdsourceHinterModule
from xmodule.vertical_module import VerticalModule, VerticalDescriptor

from . import get_test_system

import json


class CHModuleFactory(object):
    """
    Helps us make a CrowdsourceHinterModule with the specified internal
    state.
    """

    sample_problem_xml = """
    <?xml version="1.0"?>
    <crowdsource_hinter>
        <problem display_name="Numerical Input" markdown="A numerical input problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.&#10;&#10;The answer is correct if it is within a specified numerical tolerance of the expected answer.&#10;&#10;Enter the number of fingers on a human hand:&#10;= 5&#10;&#10;[explanation]&#10;If you look at your hand, you can count that you have five fingers. [explanation] " rerandomize="never" showanswer="finished">
          <p>A numerical input problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.</p>
          <p>The answer is correct if it is within a specified numerical tolerance of the expected answer.</p>
          <p>Enter the number of fingers on a human hand:</p>
          <numericalresponse answer="5">
            <formulaequationinput/>
          </numericalresponse>
          <solution>
            <div class="detailed-solution">
              <p>Explanation</p>
              <p>If you look at your hand, you can count that you have five fingers. </p>
            </div>
          </solution>
        </problem>
    </crowdsource_hinter>
    """

    num = 0

    @staticmethod
    def next_num():
        """
        Helps make unique names for our mock CrowdsourceHinterModule's
        """
        CHModuleFactory.num += 1
        return CHModuleFactory.num

    @staticmethod
    def create(hints=None,
               previous_answers=None,
               user_voted=None,
               moderate=None,
               mod_queue=None):
        """
        A factory method for making CHM's
        """
        model_data = {'data': CHModuleFactory.sample_problem_xml}

        if hints is not None:
            model_data['hints'] = hints
        else:
            model_data['hints'] = {
                '24.0': {'0': ['Best hint', 40],
                         '3': ['Another hint', 30],
                         '4': ['A third hint', 20],
                         '6': ['A less popular hint', 3]},
                '25.0': {'1': ['Really popular hint', 100]}
            }

        if mod_queue is not None:
            model_data['mod_queue'] = mod_queue
        else:
            model_data['mod_queue'] = {
                '24.0': {'2': ['A non-approved hint']},
                '26.0': {'5': ['Another non-approved hint']}
            }

        if previous_answers is not None:
            model_data['previous_answers'] = previous_answers
        else:
            model_data['previous_answers'] = [
                ['24.0', [0, 3, 4]],
                ['29.0', [None, None, None]]
            ]

        if user_voted is not None:
            model_data['user_voted'] = user_voted

        if moderate is not None:
            model_data['moderate'] = moderate

        descriptor = Mock(weight="1")
        system = get_test_system()
        module = CrowdsourceHinterModule(system, descriptor, model_data)

        return module


class VerticalWithModulesFactory(object):
    """
    Makes a vertical with several crowdsourced hinter modules inside.
    Used to make sure that several crowdsourced hinter modules can co-exist
    on one vertical.
    """

    sample_problem_xml = """<?xml version="1.0"?>
    <vertical display_name="Test vertical">
        <crowdsource_hinter>
            <problem display_name="Numerical Input" markdown=" " rerandomize="never" showanswer="finished">
              <p>Test numerical problem.</p>
              <numericalresponse answer="5">
                <formulaequationinput/>
              </numericalresponse>
              <solution>
                <div class="detailed-solution">
                  <p>Explanation</p>
                  <p>If you look at your hand, you can count that you have five fingers. </p>
                </div>
              </solution>
            </problem>
        </crowdsource_hinter>

        <crowdsource_hinter>
            <problem display_name="Numerical Input" markdown=" " rerandomize="never" showanswer="finished">
              <p>Another test numerical problem.</p>
              <numericalresponse answer="5">
                <formulaequationinput/>
              </numericalresponse>
              <solution>
                <div class="detailed-solution">
                  <p>Explanation</p>
                  <p>If you look at your hand, you can count that you have five fingers. </p>
                </div>
              </solution>
            </problem>
        </crowdsource_hinter>
    </vertical>
    """

    num = 0

    @staticmethod
    def next_num():
        CHModuleFactory.num += 1
        return CHModuleFactory.num

    @staticmethod
    def create():
        model_data = {'data': VerticalWithModulesFactory.sample_problem_xml}
        system = get_test_system()
        descriptor = VerticalDescriptor.from_xml(VerticalWithModulesFactory.sample_problem_xml, system)
        module = VerticalModule(system, descriptor, model_data)

        return module


class FakeChild(object):
    """
    A fake Xmodule.
    """
    def __init__(self):
        self.system = Mock()
        self.system.ajax_url = 'this/is/a/fake/ajax/url'

    def get_html(self):
        """
        Return a fake html string.
        """
        return 'This is supposed to be test html.'


class CrowdsourceHinterTest(unittest.TestCase):
    """
    In the below tests, '24.0' represents a wrong answer, and '42.5' represents
    a correct answer.
    """

    def test_gethtml(self):
        """
        A simple test of get_html - make sure it returns the html of the inner
        problem.
        """
        mock_module = CHModuleFactory.create()

        def fake_get_display_items():
            """
            A mock of get_display_items
            """
            return [FakeChild()]
        mock_module.get_display_items = fake_get_display_items
        out_html = mock_module.get_html()
        self.assertTrue('This is supposed to be test html.' in out_html)
        self.assertTrue('this/is/a/fake/ajax/url' in out_html)

    def test_gethtml_nochild(self):
        """
        get_html, except the module has no child :(  Should return a polite
        error message.
        """
        mock_module = CHModuleFactory.create()

        def fake_get_display_items():
            """
            Returns no children.
            """
            return []
        mock_module.get_display_items = fake_get_display_items
        out_html = mock_module.get_html()
        self.assertTrue('Error in loading crowdsourced hinter' in out_html)

    @unittest.skip("Needs to be finished.")
    def test_gethtml_multiple(self):
        """
        Makes sure that multiple crowdsourced hinters play nice, when get_html
        is called.
        NOT WORKING RIGHT NOW
        """
        mock_module = VerticalWithModulesFactory.create()
        out_html = mock_module.get_html()
        print out_html
        self.assertTrue('Test numerical problem.' in out_html)
        self.assertTrue('Another test numerical problem.' in out_html)

    def test_gethint_0hint(self):
        """
        Someone asks for a hint, when there's no hint to give.
        - Output should be blank.
        - New entry should be added to previous_answers
        """
        mock_module = CHModuleFactory.create()
        json_in = {'problem_name': '26.0'}
        out = mock_module.get_hint(json_in)
        self.assertTrue(out is None)
        self.assertTrue(['26.0', [None, None, None]] in mock_module.previous_answers)

    def test_gethint_unparsable(self):
        """
        Someone submits a hint that cannot be parsed into a float.
        - The answer should not be added to previous_answers.
        """
        mock_module = CHModuleFactory.create()
        old_answers = copy.deepcopy(mock_module.previous_answers)
        json_in = {'problem_name': 'fish'}
        out = mock_module.get_hint(json_in)
        self.assertTrue(out is None)
        self.assertTrue(mock_module.previous_answers == old_answers)

    def test_gethint_1hint(self):
        """
        Someone asks for a hint, with exactly one hint in the database.
        Output should contain that hint.
        """
        mock_module = CHModuleFactory.create()
        json_in = {'problem_name': '25.0'}
        out = mock_module.get_hint(json_in)
        self.assertTrue(out['best_hint'] == 'Really popular hint')

    def test_gethint_manyhints(self):
        """
        Someone asks for a hint, with many matching hints in the database.
        - The top-rated hint should be returned.
        - Two other random hints should be returned.
        Currently, the best hint could be returned twice - need to fix this
        in implementation.
        """
        mock_module = CHModuleFactory.create()
        json_in = {'problem_name': '24.0'}
        out = mock_module.get_hint(json_in)
        self.assertTrue(out['best_hint'] == 'Best hint')
        self.assertTrue('rand_hint_1' in out)
        self.assertTrue('rand_hint_2' in out)

    def test_getfeedback_0wronganswers(self):
        """
        Someone has gotten the problem correct on the first try.
        Output should be empty.
        """
        mock_module = CHModuleFactory.create(previous_answers=[])
        json_in = {'problem_name': '42.5'}
        out = mock_module.get_feedback(json_in)
        self.assertTrue(out is None)

    def test_getfeedback_1wronganswer_nohints(self):
        """
        Someone has gotten the problem correct, with one previous wrong
        answer.  However, we don't actually have hints for this problem.
        There should be a dialog to submit a new hint.
        """
        mock_module = CHModuleFactory.create(previous_answers=[['26.0', [None, None, None]]])
        json_in = {'problem_name': '42.5'}
        out = mock_module.get_feedback(json_in)
        print out['index_to_answer']
        self.assertTrue(out['index_to_hints'][0] == [])
        self.assertTrue(out['index_to_answer'][0] == '26.0')

    def test_getfeedback_1wronganswer_withhints(self):
        """
        Same as above, except the user did see hints.  There should be
        a voting dialog, with the correct choices, plus a hint submission
        dialog.
        """
        mock_module = CHModuleFactory.create(previous_answers=[['24.0', [0, 3, None]]])
        json_in = {'problem_name': '42.5'}
        out = mock_module.get_feedback(json_in)
        print out['index_to_hints']
        self.assertTrue(len(out['index_to_hints'][0]) == 2)

    def test_getfeedback_missingkey(self):
        """
        Someone gets a problem correct, but one of the hints that he saw
        earlier (pk=100) has been deleted.  Should just skip that hint.
        """
        mock_module = CHModuleFactory.create(
            previous_answers=[['24.0', [0, 100, None]]])
        json_in = {'problem_name': '42.5'}
        out = mock_module.get_feedback(json_in)
        self.assertTrue(len(out['index_to_hints'][0]) == 1)

    def test_vote_nopermission(self):
        """
        A user tries to vote for a hint, but he has already voted!
        Should not change any vote tallies.
        """
        mock_module = CHModuleFactory.create(user_voted=True)
        json_in = {'answer': 0, 'hint': 1}
        old_hints = copy.deepcopy(mock_module.hints)
        mock_module.tally_vote(json_in)
        self.assertTrue(mock_module.hints == old_hints)

    def test_vote_withpermission(self):
        """
        A user votes for a hint.
        Also tests vote result rendering.
        """
        mock_module = CHModuleFactory.create(
            previous_answers=[['24.0', [0, 3, None]]])
        json_in = {'answer': 0, 'hint': 3}
        dict_out = mock_module.tally_vote(json_in)
        self.assertTrue(mock_module.hints['24.0']['0'][1] == 40)
        self.assertTrue(mock_module.hints['24.0']['3'][1] == 31)
        self.assertTrue(['Best hint', 40] in dict_out['hint_and_votes'])
        self.assertTrue(['Another hint', 31] in dict_out['hint_and_votes'])

    def test_submithint_nopermission(self):
        """
        A user tries to submit a hint, but he has already voted.
        """
        mock_module = CHModuleFactory.create(user_voted=True)
        json_in = {'answer': 1, 'hint': 'This is a new hint.'}
        print mock_module.user_voted
        mock_module.submit_hint(json_in)
        print mock_module.hints
        self.assertTrue('29.0' not in mock_module.hints)

    def test_submithint_withpermission_new(self):
        """
        A user submits a hint to an answer for which no hints
        exist yet.
        """
        mock_module = CHModuleFactory.create()
        json_in = {'answer': 1, 'hint': 'This is a new hint.'}
        mock_module.submit_hint(json_in)
        self.assertTrue('29.0' in mock_module.hints)

    def test_submithint_withpermission_existing(self):
        """
        A user submits a hint to an answer that has other hints
        already.
        """
        mock_module = CHModuleFactory.create(previous_answers=[['25.0', [1, None, None]]])
        json_in = {'answer': 0, 'hint': 'This is a new hint.'}
        mock_module.submit_hint(json_in)
        # Make a hint request.
        json_in = {'problem name': '25.0'}
        out = mock_module.get_hint(json_in)
        self.assertTrue((out['best_hint'] == 'This is a new hint.')
                        or (out['rand_hint_1'] == 'This is a new hint.'))

    def test_submithint_moderate(self):
        """
        A user submits a hint, but moderation is on.  The hint should
        show up in the mod_queue, not the public-facing hints
        dict.
        """
        mock_module = CHModuleFactory.create(moderate='True')
        json_in = {'answer': 1, 'hint': 'This is a new hint.'}
        mock_module.submit_hint(json_in)
        self.assertTrue('29.0' not in mock_module.hints)
        self.assertTrue('29.0' in mock_module.mod_queue)

    def test_submithint_escape(self):
        """
        Make sure that hints are being html-escaped.
        """
        mock_module = CHModuleFactory.create()
        json_in = {'answer': 1, 'hint': '<script> alert("Trololo"); </script>'}
        mock_module.submit_hint(json_in)
        print mock_module.hints
        self.assertTrue(mock_module.hints['29.0'][0][0] == u'&lt;script&gt; alert(&quot;Trololo&quot;); &lt;/script&gt;')

    def test_template_gethint(self):
        """
        Test the templates for get_hint.
        """
        mock_module = CHModuleFactory.create()

        def fake_get_hint(get):
            """
            Creates a rendering dictionary, with which we can test
            the templates.
            """
            return {'best_hint': 'This is the best hint.',
                    'rand_hint_1': 'A random hint',
                    'rand_hint_2': 'Another random hint',
                    'answer': '42.5'}

        mock_module.get_hint = fake_get_hint
        json_in = {'problem_name': '42.5'}
        out = json.loads(mock_module.handle_ajax('get_hint', json_in))['contents']
        self.assertTrue('This is the best hint.' in out)
        self.assertTrue('A random hint' in out)
        self.assertTrue('Another random hint' in out)

    def test_template_feedback(self):
        """
        Test the templates for get_feedback.
        NOT FINISHED

        from lxml import etree
        mock_module = CHModuleFactory.create()

        def fake_get_feedback(get):
            index_to_answer = {'0': '42.0', '1': '9000.01'}
            index_to_hints = {'0': [('A hint for 42', 12),
                                    ('Another hint for 42', 14)],
                              '1': [('A hint for 9000.01', 32)]}
            return {'index_to_hints': index_to_hints, 'index_to_answer': index_to_answer}

        mock_module.get_feedback = fake_get_feedback
        json_in = {'problem_name': '42.5'}
        out = json.loads(mock_module.handle_ajax('get_feedback', json_in))['contents']
        html_tree = etree.XML(out)
        # To be continued...

        """
        pass
