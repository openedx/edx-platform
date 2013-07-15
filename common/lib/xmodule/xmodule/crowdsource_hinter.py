"""
Adds crowdsourced hinting functionality to lon-capa numerical response problems.

Currently experimental - not for instructor use, yet.
"""

import logging
import json
import random

from pkg_resources import resource_string

from lxml import etree

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String, Integer, Boolean, Dict, List

from capa.responsetypes import FormulaResponse, StudentInputError

from django.utils.html import escape

log = logging.getLogger(__name__)


class CrowdsourceHinterFields(object):
    """Defines fields for the crowdsource hinter module."""
    has_children = True

    moderate = String(help='String "True"/"False" - activates moderation', scope=Scope.content,
                      default='False')
    debug = String(help='String "True"/"False" - allows multiple voting', scope=Scope.content,
                   default='False')
    # Usage: hints[answer] = {str(pk): [hint_text, #votes]}
    # hints is a dictionary that takes answer keys.
    # Each value is itself a dictionary, accepting hint_pk strings as keys,
    # and returning [hint text, #votes] pairs as values
    hints = Dict(help='A dictionary containing all the active hints.', scope=Scope.content, default={})
    mod_queue = Dict(help='A dictionary containing hints still awaiting approval', scope=Scope.content,
                     default={})
    hint_pk = Integer(help='Used to index hints.', scope=Scope.content, default=0)
    # signature_to_ans maps an answer signature to an answer string that shows that answer in a
    # human-readable form.
    signature_to_ans = Dict(help='Maps a signature to a representative formula.', scope=Scope.content,
                            default={})
    # A list of dictionaries, each of which represents an n-dimenstional point that we plug into
    # formulas.  Each dictionary maps variables to values, eg {'x': 5.1}.
    formula_test_values = List(help='The values that we plug into formula responses', scope=Scope.content,
                               default=[])
    # A list of previous answers this student made to this problem.
    # Of the form [answer, [hint_pk_1, hint_pk_2, hint_pk_3]] for each problem.  hint_pk's are
    # None if the hint was not given.
    previous_answers = List(help='A list of previous submissions.', scope=Scope.user_state, default=[])
    user_voted = Boolean(help='Specifies if the user has voted on this problem or not.',
                         scope=Scope.user_state, default=False)


class CrowdsourceHinterModule(CrowdsourceHinterFields, XModule):
    """
    An Xmodule that makes crowdsourced hints.
    Currently, only works on capa problems with exactly one numerical response,
    and no other parts.

    Example usage:
    <crowdsource_hinter>
        <problem blah blah />
    </crowdsource_hinter>

    XML attributes:
    -moderate="True" will not display hints until staff approve them in the hint manager.
    -debug="True" will let users vote as often as they want.
    """
    icon_class = 'crowdsource_hinter'
    css = {'scss': [resource_string(__name__, 'css/crowdsource_hinter/display.scss')]}
    js = {'coffee': [resource_string(__name__, 'js/src/crowdsource_hinter/display.coffee')],
          'js': []}
    js_module_name = "Hinter"

    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)
        # We need to know whether we are working with a FormulaResponse problem.
        self.is_formula = (type(self.get_display_items()[0].lcp.responders.values()[0]) == FormulaResponse)
        if self.is_formula:
            self.answer_to_str = self.formula_answer_to_str
            self.answer_signature = self.formula_answer_signature
        else:
            self.answer_to_str = self.numerical_answer_to_str
            # Right now, numerical problems don't need special answer signature treatment.
            self.answer_signature = lambda x: x

    def get_html(self):
        """
        Puts a wrapper around the problem html.  This wrapper includes ajax urls of the
        hinter and of the problem.
        - Dependent on lon-capa problem.
        """
        if self.debug == 'True':
            # Reset the user vote, for debugging only!
            self.user_voted = False
        if self.hints == {}:
            # Force self.hints to be written into the database.  (When an xmodule is initialized,
            # fields are not added to the db until explicitly changed at least once.)
            self.hints = {}

        try:
            child = self.get_display_items()[0]
            out = child.get_html()
            # The event listener uses the ajax url to find the child.
            child_url = child.system.ajax_url
        except IndexError:
            out = 'Error in loading crowdsourced hinter - can\'t find child problem.'
            child_url = ''

        # Wrap the module in a <section>.  This lets us pass data attributes to the javascript.
        out += '<section class="crowdsource-wrapper" data-url="' + self.system.ajax_url +\
            '" data-child-url = "' + child_url + '"> </section>'

        return out

    def numerical_answer_to_str(self, answer):
        """
        Converts capa numerical answer format to a string representation
        of the answer.
        -Lon-capa dependent.
        -Assumes that the problem only has one part.
        """
        return str(float(answer.values()[0]))

    def formula_answer_to_str(self, answer):
        """
        Converts capa formula answer into a string.
        -Lon-capa dependent.
        -Assumes that the problem only has one part.
        """
        return str(answer.values()[0])

    def formula_answer_signature(self, answer):
        """
        Converts a capa answer string (output of formula_answer_to_str)
        to a string unique to each formula equality class.
        So, x^2 and x*x would have the same signature, which would differ
        from the signature of 2*x^2.
        """
        responder = self.get_display_items()[0].lcp.responders.values()[0]
        if self.formula_test_values == []:
            # Make a set of test values, and save them.
            self.formula_test_values = responder.randomize_variables(responder.samples)
        try:
            # TODO, maybe: add some rounding to signature generation, so that floating point
            # errors don't make a difference.
            out = str(responder.hash_answers(answer, self.formula_test_values))
        except StudentInputError:
            # I'm not sure what's the best thing to do here.  I'm returning
            # None, for now, so that the calling function has a chance to catch
            # the error without having to import StudentInputError.
            return None
        return out

    def handle_ajax(self, dispatch, data):
        """
        This is the landing method for AJAX calls.
        """
        if dispatch == 'get_hint':
            out = self.get_hint(data)
        elif dispatch == 'get_feedback':
            out = self.get_feedback(data)
        elif dispatch == 'vote':
            out = self.tally_vote(data)
        elif dispatch == 'submit_hint':
            out = self.submit_hint(data)
        else:
            return json.dumps({'contents': 'Error - invalid operation.'})

        if out is None:
            out = {'op': 'empty'}
        elif 'error' in out:
            # Error in processing.
            out.update({'op': 'error'})
        else:
            out.update({'op': dispatch})
        return json.dumps({'contents': self.system.render_template('hinter_display.html', out)})

    def get_hint(self, data):
        """
        The student got the incorrect answer found in data.  Give him a hint.

        Called by hinter javascript after a problem is graded as incorrect.
        Args:
        `data` -- must be interpretable by answer_to_str.
        Output keys:
            - 'best_hint' is the hint text with the most votes.
            - 'rand_hint_1' and 'rand_hint_2' are two random hints to the answer in `data`.
            - 'answer' is the parsed answer that was submitted.
        """
        try:
            answer = self.answer_to_str(data)
        except ValueError:
            # Sometimes, we get an answer that's just not parsable.  Do nothing.
            log.exception('Answer not parsable: ' + str(data))
            return
        # Make a signature of the answer, for formula responses.
        signature = self.answer_signature(answer)
        if signature == None:
            # Sometimes, signature conversion may fail.
            log.exception('Signature conversion failed: ' + str(answer))
            return
        # Look for a hint to give.
        # Make a local copy of self.hints - this means we only need to do one json unpacking.
        # (This is because xblocks storage makes the following command a deep copy.)
        local_hints = self.hints
        if (signature not in local_hints) or (len(local_hints[signature]) == 0):
            # No hints to give.  Return.
            self.previous_answers += [[answer, [None, None, None]]]
            return
        # Get the top hint, plus two random hints.
        n_hints = len(local_hints[signature])
        best_hint_index = max(local_hints[signature], key=lambda key: local_hints[signature][key][1])
        best_hint = local_hints[signature][best_hint_index][0]
        if len(local_hints[signature]) == 1:
            rand_hint_1 = ''
            rand_hint_2 = ''
            self.previous_answers += [[answer, [best_hint_index, None, None]]]
        elif n_hints == 2:
            best_hint = local_hints[signature].values()[0][0]
            best_hint_index = local_hints[signature].keys()[0]
            rand_hint_1 = local_hints[signature].values()[1][0]
            hint_index_1 = local_hints[signature].keys()[1]
            rand_hint_2 = ''
            self.previous_answers += [[answer, [best_hint_index, hint_index_1, None]]]
        else:
            (hint_index_1, rand_hint_1), (hint_index_2, rand_hint_2) =\
                random.sample(local_hints[signature].items(), 2)
            rand_hint_1 = rand_hint_1[0]
            rand_hint_2 = rand_hint_2[0]
            self.previous_answers += [[answer, [best_hint_index, hint_index_1, hint_index_2]]]

        return {'best_hint': best_hint,
                'rand_hint_1': rand_hint_1,
                'rand_hint_2': rand_hint_2,
                'answer': answer}

    def get_feedback(self, data):
        """
        The student got it correct.  Ask him to vote on hints, or submit a hint.

        Args:
        `data` -- not actually used.  (It is assumed that the answer is correct.)
        Output keys:
            - 'answer_to_hints': a nested dictionary.
              answer_to_hints[answer][hint_pk] returns the text of the hint.
        """
        # The student got it right.
        # Did he submit at least one wrong answer?
        if len(self.previous_answers) == 0:
            # No.  Nothing to do here.
            return
        # Make a hint-voting interface for each wrong answer.  The student will only
        # be allowed to make one vote / submission, but he can choose which wrong answer
        # he wants to look at.
        answer_to_hints = {}    # answer_to_hints[answer text][hint pk] -> hint text

        # Go through each previous answer, and populate index_to_hints and index_to_answer.
        for i in xrange(len(self.previous_answers)):
            answer, hints_offered = self.previous_answers[i]
            if answer not in answer_to_hints:
                answer_to_hints[answer] = {}
            signature = self.answer_signature(answer)
            if signature in self.hints:
                # Go through each hint, and add to index_to_hints
                for hint_id in hints_offered:
                    if (hint_id is not None) and (hint_id not in answer_to_hints[answer]):
                        try:
                            answer_to_hints[answer][hint_id] = self.hints[signature][str(hint_id)][0]
                        except KeyError:
                            # Sometimes, the hint that a user saw will have been deleted by the instructor.
                            continue

        return {'answer_to_hints': answer_to_hints}

    def tally_vote(self, data):
        """
        Tally a user's vote on his favorite hint.

        Args:
        `data` -- expected to have the following keys:
            'answer': text of answer we're voting on
            'hint': hint_pk
            'pk_list': We will return a list of how many votes each hint has so far.
                       It's up to the browser to specify which hints to return vote counts for.
                       Every pk listed here will have a hint count returned.
        Returns key 'hint_and_votes', a list of (hint_text, #votes) pairs.
        """
        if self.user_voted:
            return {'error': 'Sorry, but you have already voted!'}
        ans = data['answer']
        signature = self.answer_signature(ans)
        if signature is None:
            # Uh oh.  Invalid answer.
            log.exception('Failure in hinter tally_vote: Unable to parse answer: ' + ans)
            return {'error': 'Failure in voting!'}
        hint_pk = str(data['hint'])
        pk_list = json.loads(data['pk_list'])
        # We use temp_dict because we need to do a direct write for the database to update.
        temp_dict = self.hints
        try:
            temp_dict[signature][hint_pk][1] += 1
        except KeyError:
            log.exception('Failure in hinter tally_vote: User voted for non-existant hint: Answer=' +
                          ans + ' pk=' + hint_pk)
            return {'error': 'Failure in voting!'}
        self.hints = temp_dict
        # Don't let the user vote again!
        self.user_voted = True

        # Return a list of how many votes each hint got.
        hint_and_votes = []
        for vote_pk in pk_list:
            try:
                hint_and_votes.append(temp_dict[signature][str(vote_pk)])
            except KeyError:
                log.exception('In hinter tally_vote: pk_list contains non-existant pk: ' + str(vote_pk))

        hint_and_votes.sort(key=lambda pair: pair[1], reverse=True)
        # Reset self.previous_answers.
        self.previous_answers = []
        return {'hint_and_votes': hint_and_votes}

    def submit_hint(self, data):
        """
        Take a hint submission and add it to the database.

        Args:
        `data` -- expected to have the following keys:
            'answer': text of answer
            'hint': text of the new hint that the user is adding
        Returns a thank-you message.
        """
        # Do html escaping.  Perhaps in the future do profanity filtering, etc. as well.
        hint = escape(data['hint'])
        answer = data['answer']
        signature = self.answer_signature(answer)
        if signature is None:
            log.exception('Failure in hinter submit_hint: Unable to parse answer: ' + answer)
            return {'error': 'Could not submit answer'}
        # Only allow a student to vote or submit a hint once.
        if self.user_voted:
            return {'message': 'Sorry, but you have already voted!'}
        # Add the new hint to self.hints or self.mod_queue.  (Awkward because a direct write
        # is necessary.)
        if self.moderate == 'True':
            temp_dict = self.mod_queue
        else:
            temp_dict = self.hints
        if answer in temp_dict:
            temp_dict[signature][str(self.hint_pk)] = [hint, 1]     # With one vote (the user himself).
        else:
            temp_dict[signature] = {str(self.hint_pk): [hint, 1]}
        # Add the signature to signature_to_ans, if it's not there yet.
        # This allows instructors to see a human-readable answer that corresponds to each signature.
        self.add_signature(signature, answer)
        self.hint_pk += 1
        if self.moderate == 'True':
            self.mod_queue = temp_dict
        else:
            self.hints = temp_dict
        # Mark the user has having voted; reset previous_answers
        self.user_voted = True
        self.previous_answers = []
        return {'message': 'Thank you for your hint!'}

    def add_signature(self, signature, answer):
        """
        Add a signature to self.signature_to_ans.  If the signature already
        exists, do nothing.
        """
        if signature not in self.signature_to_ans:
            local_sta = self.signature_to_ans
            local_sta[signature] = answer
            self.signature_to_ans = local_sta


class CrowdsourceHinterDescriptor(CrowdsourceHinterFields, RawDescriptor):
    module_class = CrowdsourceHinterModule
    stores_state = True

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        for child in xml_object:
            try:
                children.append(system.process_xml(etree.tostring(child, encoding='unicode')).location.url())
            except Exception as e:
                log.exception("Unable to load child when parsing CrowdsourceHinter. Continuing...")
                if system.error_tracker is not None:
                    system.error_tracker("ERROR: " + str(e))
                continue
        return {}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('crowdsource_hinter')
        for child in self.get_children():
            xml_object.append(
                etree.fromstring(child.export_to_xml(resource_fs)))
        return xml_object
