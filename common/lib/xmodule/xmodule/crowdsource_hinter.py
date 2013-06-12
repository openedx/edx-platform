import logging
import copy
import json
import os
import re
import string
import random

from pkg_resources import resource_listdir, resource_string, resource_isdir

from lxml import etree

from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.x_module import XModule
from xmodule.xml_module import XmlDescriptor
from xblock.core import XBlock, Scope, String, Integer, Float, Object, Boolean

from django.utils.html import escape

log = logging.getLogger(__name__)


class CrowdsourceHinterFields(object):
    has_children = True
    hints = Object(help='''A dictionary mapping answers to lists of [hint, number_of_votes] pairs.
    ''', scope=Scope.content, default=     {
            '4':
            [['This is a hint.', 5],
            ['This is hint 2', 3],
            ['This is hint 3', 2],
            ['This is hint 4', 1]]})
    '''
    Testing data for hints:

    '''
    previous_answers = Object(help='''A list of previous answers this student made to this problem.
        Of the form (answer, (hint_id_1, hint_id_2, hint_id_3)) for each problem.  hint_id's are
        None if the hint was not given.''',
        scope=Scope.user_state, default=[])

    user_voted = Boolean(help='Specifies if the user has voted on this problem or not.',
        scope=Scope.user_state, default=False)


class CrowdsourceHinterModule(CrowdsourceHinterFields, XModule):
    ''' An Xmodule that makes crowdsourced hints.
    '''
    icon_class = 'crowdsource_hinter'

    js = {'coffee': [resource_string(__name__, 'js/src/crowdsource_hinter/display.coffee'),
                 ],
      'js': []}
    js_module_name = "Hinter"


    def __init__(self, system, location, descriptor, model_data):
        XModule.__init__(self, system, location, descriptor, model_data)


    def get_html(self):
        '''
        Does a regular expression find and replace to change the AJAX url.
        - Dependent on lon-capa problem.
        '''
        # Reset the user vote, for debugging only!  Remove for prod.
        self.user_voted = False
        for child in self.get_display_items():
            out = child.get_html()
            # The event listener uses the ajax url to find the child.
            child_url = child.system.ajax_url
            break
        # Wrap the module in a <section>.  This lets us pass data attributes to the javascript.
        out += '<section class="crowdsource-wrapper" data-url="' + self.system.ajax_url +\
            '" data-child-url = "' + child_url + '"> </section>'
        return out

    def capa_make_answer_hashable(self, answer):
        '''
        Capa answer format: dict[problem name] -> [list of answers]
        Output format: ((problem name, (answers)))
        '''
        out = []
        for problem, a in answer.items():
            out.append((problem, tuple(a)))
        return str(tuple(sorted(out)))


    def ans_to_text(self, answer):
        '''
        Converts capa answer format to a string representation
        of the answer.
        -Lon-capa dependent.
        '''
        return answer.values()[0][0]


    def handle_ajax(self, dispatch, get):
        '''
        This is the landing method for AJAX calls.
        '''
        if dispatch == 'get_hint':
            return self.get_hint(get)
        if dispatch == 'get_feedback':
            return self.get_feedback(get)
        if dispatch == 'vote':
            return self.tally_vote(get)
        if dispatch == 'submit_hint':
            return self.submit_hint(get)

    def get_hint(self, get):
        '''
        The student got the incorrect answer found in get.  Give him a hint.
        '''
        print self.hints
        answer = self.ans_to_text(get)
        # Look for a hint to give.
        if answer not in self.hints:
            # No hints to give.  Return.
            self.previous_answers += [(answer, (None, None, None))]
            return json.dumps({'contents': ' '})
        # Get the top hint, plus two random hints.
        n_hints = len(self.hints[answer])
        best_hint_index = max(xrange(n_hints), key=lambda i:self.hints[answer][i][1])
        best_hint = self.hints[answer][best_hint_index][0]
        if len(self.hints[answer]) == 1:
            rand_hint_1 = ''
            rand_hint_2 = ''
            self.previous_answers += [(answer, (0, None, None))]
        elif len(self.hints[answer]) == 2:
            best_hint = self.hints[answer][0][0]
            rand_hint_1 = self.hints[answer][1][0]
            rand_hint_2 = ''
            self.previous_answers += [(answer, (0, 1, None))]
        else:
            hint_index_1, hint_index_2 = random.sample(xrange(len(self.hints[answer])), 2)
            rand_hint_1 = self.hints[answer][hint_index_1][0]
            rand_hint_2 = self.hints[answer][hint_index_2][0]
            self.previous_answers += [(answer, (best_hint_index, hint_index_1, hint_index_2))]
        hint_text = best_hint + '<br />' + rand_hint_1 + '<br />' + rand_hint_2
        return json.dumps({'contents': hint_text})

    def get_feedback(self, get):
        '''
        The student got it correct.  Ask him to vote on hints, or submit a hint.
        '''
        # The student got it right.
        # Did he submit at least one wrong answer?
        out = ' '
        if len(self.previous_answers) == 0:
            # No.  Nothing to do here.
            return json.dumps({'contents': out})
        # Make a hint-voting interface for each wrong answer.  The student will only
        # be allowed to make one vote / submission, but he can choose which wrong answer
        # he wants to look at.
        pretty_answers = []
        for i in xrange(len(self.previous_answers)):
            answer, hints_offered = self.previous_answers[i]
            pretty_answers.append(answer)
            # If there are previous hints for this answer, ask the student to vote on one.
            if answer in self.hints:
                out += '<div class = "previous-answer" id="previous-answer-' + str(i) + \
                '" style="display:none"> Which hint was most helpful when you got the wrong answer of '\
                    + answer + '?'
                # Add each hint to the html string, with a vote button.
                for j, hint_id in enumerate(hints_offered):
                    if hint_id != None:
                        out += '<br /><input class="vote" data-answer="'+str(i)+'" data-hintno="'+str(j)+\
                            '" type="button" value="Vote"> ' + self.hints[answer][hint_id][0]
                        

            # Or, let the student create his own hint
            out += '''<br /> If you didn\'t like any of these, plese submit your own: <br />
                <textarea cols="50" id="custom-hint-'''+str(i)+'''">
What would you say to help someone who got this wrong answer?
(Don't give away the answer, please.)
                </textarea>'''

            out += '<input class="submit-hint" data-answer="' + str(i) + '" type="button" value="submit">'

            # Close the .previous-answer div.
            out += '</div>'

        # Add preamble.
        out2 = '''Help us improve our hinting system by voting on the hint that was most helpful 
            to you.  Start by picking one of your previous incorrect answers from below: <br />
            <select id="feedback-select">'''
        for i, answer in enumerate(pretty_answers):
            out2 += '<option value=' + str(i) + '>' + str(answer) + '</option>'
        out2 += '</select><br />'
        return json.dumps({'contents': out2 + out})


    def tally_vote(self, get):
        '''
        Tally a user's vote on his favorite hint.
        get:
            'answer': ans_no (index in previous_answers)
            'hint': hint_no
        '''
        if self.user_voted:
           return json.dumps({'contents': 'Sorry, but you have already voted!'})
        ans_no = int(get['answer']) 
        hint_no = int(get['hint'])
        answer = self.previous_answers[ans_no][0]
        temp_dict = self.hints
        temp_dict[answer][hint_no][1] += 1
        # Awkward, but you need to do a direct write for the database to update.
        self.hints = temp_dict
        # Don't let the user vote again!
        self.user_voted = True
        # Reset self.previous_answers.
        self.previous_answers = []
        # In the future, return a list of how many votes each hint got, maybe?
        return json.dumps({'contents': 'Congrats, you\'ve voted!'})


    def submit_hint(self, get):
        '''
        Take a hint submission and add it to the database.
        get:
            'answer': answer index in previous_answers
            'hint': text of the new hint that the user is adding
        '''
        # Do html escaping.  Perhaps in the future do profanity filtering, etc. as well.
        hint = escape(get['hint'])
        answer = self.previous_answers[int(get['answer'])][0]
        # Add the new hint to self.hints.  (Awkward because a direct write 
        # is necessary.)
        temp_dict = self.hints
        temp_dict[answer].append([hint, 1])     # With one vote (the user himself).
        self.hints = temp_dict
        # Mark the user has having voted; reset previous_answers
        self.user_voted = True
        self.previous_answers = []
        return json.dumps({'contents': 'Thank you for your hint!'})


class CrowdsourceHinterDescriptor(CrowdsourceHinterFields, XmlDescriptor):
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