"""
Tests the crowdsourced hinter xmodule.
"""

from mock import Mock, MagicMock
import unittest
import copy

from xmodule.crowdsource_hinter import CrowdsourceHinterModule
from xmodule.vertical_block import VerticalBlock
from xmodule.x_module import STUDENT_VIEW
from xblock.field_data import DictFieldData
from xblock.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import ScopeIds

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
               user_submissions=None,
               user_voted=None,
               moderate=None,
               mod_queue=None):
        """
        A factory method for making CHM's
        """
        # Should have a single child, but it doesn't matter what that child is
        field_data = {'data': CHModuleFactory.sample_problem_xml, 'children': [None]}

        if hints is not None:
            field_data['hints'] = hints
        else:
            field_data['hints'] = {
                '24.0': {'0': ['Best hint', 40],
                         '3': ['Another hint', 30],
                         '4': ['A third hint', 20],
                         '6': ['A less popular hint', 3]},
                '25.0': {'1': ['Really popular hint', 100]}
            }

        if mod_queue is not None:
            field_data['mod_queue'] = mod_queue
        else:
            field_data['mod_queue'] = {
                '24.0': {'2': ['A non-approved hint']},
                '26.0': {'5': ['Another non-approved hint']}
            }

        if previous_answers is not None:
            field_data['previous_answers'] = previous_answers
        else:
            field_data['previous_answers'] = [
                ['24.0', [0, 3, 4]],
                ['29.0', []]
            ]

        if user_submissions is not None:
            field_data['user_submissions'] = user_submissions
        else:
            field_data['user_submissions'] = ['24.0', '29.0']

        if user_voted is not None:
            field_data['user_voted'] = user_voted

        if moderate is not None:
            field_data['moderate'] = moderate

        descriptor = Mock(weight='1')
        # Make the descriptor have a capa problem child.
        capa_descriptor = MagicMock()
        capa_descriptor.name = 'capa'
        capa_descriptor.displayable_items.return_value = [capa_descriptor]
        descriptor.get_children.return_value = [capa_descriptor]

        # Make a fake capa module.
        capa_module = MagicMock()
        capa_module.lcp = MagicMock()
        responder = MagicMock()

        def validate_answer(answer):
            """ A mock answer validator - simulates a numerical response"""
            try:
                float(answer)
                return True
            except ValueError:
                return False
        responder.validate_answer = validate_answer

        def compare_answer(ans1, ans2):
            """ A fake answer comparer """
            return ans1 == ans2
        responder.compare_answer = compare_answer

        capa_module.lcp.responders = {'responder0': responder}
        capa_module.displayable_items.return_value = [capa_module]

        system = get_test_system()
        # Make the system have a marginally-functional get_module

        def fake_get_module(descriptor):
            """
            A fake module-maker.
            """
            return capa_module
        system.get_module = fake_get_module
        module = CrowdsourceHinterModule(descriptor, system, DictFieldData(field_data), Mock())

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
        """Increments a global counter for naming."""
        CHModuleFactory.num += 1
        return CHModuleFactory.num

    @staticmethod
    def create():
        """Make a vertical."""
        field_data = {'data': VerticalWithModulesFactory.sample_problem_xml}
        system = get_test_system()
        descriptor = VerticalBlock.parse_xml(VerticalWithModulesFactory.sample_problem_xml, system)
        module = VerticalBlock(system, descriptor, field_data)

        return module


class FakeChild(XBlock):
    """
    A fake Xmodule.
    """
    def __init__(self):
        self.runtime = get_test_system()
        self.student_view = Mock(return_value=Fragment(self.get_html()))
        self.save = Mock()
        self.id = 'i4x://this/is/a/fake/id'
        self.scope_ids = ScopeIds('fake_user_id', 'fake_block_type', 'fake_definition_id', 'fake_usage_id')

    def get_html(self):
        """
        Return a fake html string.
        """
        return u'This is supposed to be test html.'


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
        out_html = mock_module.render(STUDENT_VIEW).content
        self.assertTrue('This is supposed to be test html.' in out_html)
        self.assertTrue('i4x://this/is/a/fake/id' in out_html)

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
        out_html = mock_module.render(STUDENT_VIEW).content
        self.assertTrue('Error in loading crowdsourced hinter' in out_html)

    @unittest.skip("Needs to be finished.")
    def test_gethtml_multiple(self):
        """
        Makes sure that multiple crowdsourced hinters play nice, when get_html
        is called.
        NOT WORKING RIGHT NOW
        """
        mock_module = VerticalWithModulesFactory.create()
        out_html = mock_module.render(STUDENT_VIEW).content
        self.assertTrue('Test numerical problem.' in out_html)
        self.assertTrue('Another test numerical problem.' in out_html)

    def test_numerical_answer_to_str(self):
        """
        Tests the get request to string converter for numerical responses.
        """
        mock_module = CHModuleFactory.create()
        get = {'response1': '4'}
        parsed = mock_module.numerical_answer_to_str(get)
        self.assertTrue(parsed == '4')

    def test_formula_answer_to_str(self):
        """
        Tests the get request to string converter for formula responses.
        """
        mock_module = CHModuleFactory.create()
        get = {'response1': 'x*y^2'}
        parsed = mock_module.formula_answer_to_str(get)
        self.assertTrue(parsed == 'x*y^2')

    def test_gethint_0hint(self):
        """
        Someone asks for a hint, when there's no hint to give.
        - Output should be blank.
        - New entry should be added to previous_answers
        """
        mock_module = CHModuleFactory.create()
        json_in = {'problem_name': '26.0'}
        out = mock_module.get_hint(json_in)
        print mock_module.previous_answers
        self.assertTrue(out is None)
        self.assertTrue('26.0' in mock_module.user_submissions)

    def test_gethint_unparsable(self):
        """
        Someone submits an answer that is in the wrong format.
        - The answer should not be added to previous_answers.
        """
        mock_module = CHModuleFactory.create()
        old_answers = copy.deepcopy(mock_module.previous_answers)
        json_in = 'blah'
        out = mock_module.get_hint(json_in)
        self.assertTrue(out is None)
        self.assertTrue(mock_module.previous_answers == old_answers)

    def test_gethint_signature_error(self):
        """
        Someone submits an answer that cannot be calculated as a float.
        Nothing should change.
        """
        mock_module = CHModuleFactory.create()
        old_answers = copy.deepcopy(mock_module.previous_answers)
        old_user_submissions = copy.deepcopy(mock_module.user_submissions)
        json_in = {'problem1': 'fish'}
        out = mock_module.get_hint(json_in)
        self.assertTrue(out is None)
        self.assertTrue(mock_module.previous_answers == old_answers)
        self.assertTrue(mock_module.user_submissions == old_user_submissions)

    def test_gethint_1hint(self):
        """
        Someone asks for a hint, with exactly one hint in the database.
        Output should contain that hint.
        """
        mock_module = CHModuleFactory.create()
        json_in = {'problem_name': '25.0'}
        out = mock_module.get_hint(json_in)
        self.assertTrue('Really popular hint' in out['hints'])
        # Also make sure that the input gets added to user_submissions,
        # and that the hint is logged in previous_answers.
        self.assertTrue('25.0' in mock_module.user_submissions)
        self.assertTrue(['25.0', ['1']] in mock_module.previous_answers)

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
        self.assertTrue('Best hint' in out['hints'])
        self.assertTrue(len(out['hints']) == 3)

    def test_getfeedback_0wronganswers(self):
        """
        Someone has gotten the problem correct on the first try.
        Output should be empty.
        """
        mock_module = CHModuleFactory.create(previous_answers=[], user_submissions=[])
        json_in = {'problem_name': '42.5'}
        out = mock_module.get_feedback(json_in)
        print out
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
        self.assertTrue(out['answer_to_hints'] == {'26.0': {}})

    def test_getfeedback_1wronganswer_withhints(self):
        """
        Same as above, except the user did see hints.  There should be
        a voting dialog, with the correct choices, plus a hint submission
        dialog.
        """
        mock_module = CHModuleFactory.create(previous_answers=[['24.0', [0, 3, None]]])
        json_in = {'problem_name': '42.5'}
        out = mock_module.get_feedback(json_in)
        self.assertTrue(len(out['answer_to_hints']['24.0']) == 2)

    def test_getfeedback_missingkey(self):
        """
        Someone gets a problem correct, but one of the hints that he saw
        earlier (pk=100) has been deleted.  Should just skip that hint.
        """
        mock_module = CHModuleFactory.create(
            previous_answers=[['24.0', [0, 100, None]]])
        json_in = {'problem_name': '42.5'}
        out = mock_module.get_feedback(json_in)
        self.assertTrue(len(out['answer_to_hints']['24.0']) == 1)

    def test_vote_nopermission(self):
        """
        A user tries to vote for a hint, but he has already voted!
        Should not change any vote tallies.
        """
        mock_module = CHModuleFactory.create(user_voted=True)
        json_in = {'answer': '24.0', 'hint': 1, 'pk_list': json.dumps([['24.0', 1], ['24.0', 3]])}
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
        json_in = {'answer': '24.0', 'hint': 3, 'pk_list': json.dumps([['24.0', 0], ['24.0', 3]])}
        dict_out = mock_module.tally_vote(json_in)
        self.assertTrue(mock_module.hints['24.0']['0'][1] == 40)
        self.assertTrue(mock_module.hints['24.0']['3'][1] == 31)
        self.assertTrue(['Best hint', 40] in dict_out['hint_and_votes'])
        self.assertTrue(['Another hint', 31] in dict_out['hint_and_votes'])

    def test_vote_unparsable(self):
        """
        A user somehow votes for an unparsable answer.
        Should return a friendly error.
        (This is an unusual exception path - I don't know how it occurs,
        except if you manually make a post request.  But, it seems to happen
        occasionally.)
        """
        mock_module = CHModuleFactory.create()
        # None means that the answer couldn't be parsed.
        mock_module.answer_signature = lambda text: None
        json_in = {'answer': 'fish', 'hint': 3, 'pk_list': '[]'}
        dict_out = mock_module.tally_vote(json_in)
        print dict_out
        self.assertTrue(dict_out == {'error': 'Failure in voting!'})

    def test_vote_nohint(self):
        """
        A user somehow votes for a hint that doesn't exist.
        Should return a friendly error.
        """
        mock_module = CHModuleFactory.create()
        json_in = {'answer': '24.0', 'hint': '25', 'pk_list': '[]'}
        dict_out = mock_module.tally_vote(json_in)
        self.assertTrue(dict_out == {'error': 'Failure in voting!'})

    def test_vote_badpklist(self):
        """
        Some of the pk's specified in pk_list are invalid.
        Should just skip those.
        """
        mock_module = CHModuleFactory.create()
        json_in = {'answer': '24.0', 'hint': '0', 'pk_list': json.dumps([['24.0', 0], ['24.0', 12]])}
        hint_and_votes = mock_module.tally_vote(json_in)['hint_and_votes']
        self.assertTrue(['Best hint', 41] in hint_and_votes)
        self.assertTrue(len(hint_and_votes) == 1)

    def test_submithint_nopermission(self):
        """
        A user tries to submit a hint, but he has already voted.
        """
        mock_module = CHModuleFactory.create(user_voted=True)
        json_in = {'answer': '29.0', 'hint': 'This is a new hint.'}
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
        json_in = {'answer': '29.0', 'hint': 'This is a new hint.'}
        mock_module.submit_hint(json_in)
        self.assertTrue('29.0' in mock_module.hints)

    def test_submithint_withpermission_existing(self):
        """
        A user submits a hint to an answer that has other hints
        already.
        """
        mock_module = CHModuleFactory.create(previous_answers=[['25.0', [1, None, None]]])
        json_in = {'answer': '25.0', 'hint': 'This is a new hint.'}
        mock_module.submit_hint(json_in)
        # Make a hint request.
        json_in = {'problem name': '25.0'}
        out = mock_module.get_hint(json_in)
        self.assertTrue('This is a new hint.' in out['hints'])

    def test_submithint_moderate(self):
        """
        A user submits a hint, but moderation is on.  The hint should
        show up in the mod_queue, not the public-facing hints
        dict.
        """
        mock_module = CHModuleFactory.create(moderate='True')
        json_in = {'answer': '29.0', 'hint': 'This is a new hint.'}
        mock_module.submit_hint(json_in)
        self.assertTrue('29.0' not in mock_module.hints)
        self.assertTrue('29.0' in mock_module.mod_queue)

    def test_submithint_escape(self):
        """
        Make sure that hints are being html-escaped.
        """
        mock_module = CHModuleFactory.create()
        json_in = {'answer': '29.0', 'hint': '<script> alert("Trololo"); </script>'}
        mock_module.submit_hint(json_in)
        self.assertTrue(mock_module.hints['29.0']['0'][0] == u'&lt;script&gt; alert(&quot;Trololo&quot;); &lt;/script&gt;')

    def test_submithint_unparsable(self):
        mock_module = CHModuleFactory.create()
        mock_module.answer_signature = lambda text: None
        json_in = {'answer': 'fish', 'hint': 'A hint'}
        dict_out = mock_module.submit_hint(json_in)
        print dict_out
        print mock_module.hints
        self.assertTrue('error' in dict_out)
        self.assertTrue(None not in mock_module.hints)
        self.assertTrue('fish' not in mock_module.hints)

    def test_template_gethint(self):
        """
        Test the templates for get_hint.
        """
        mock_module = CHModuleFactory.create()

        def fake_get_hint(_):
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
