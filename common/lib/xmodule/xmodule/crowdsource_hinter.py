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
from xblock.core import XBlock, Scope, String, Integer, Float, Boolean, Dict, List

from django.utils.html import escape

log = logging.getLogger(__name__)


class CrowdsourceHinterFields(object):
    has_children = True
    hints = Dict(help='''A dictionary mapping answers to lists of [hint, number_of_votes] pairs.
    ''', scope=Scope.content, default= {})

    previous_answers = List(help='''A list of previous answers this student made to this problem.
        Of the form (answer, (hint_id_1, hint_id_2, hint_id_3)) for each problem.  hint_id's are
        None if the hint was not given.''',
        scope=Scope.user_state, default=[])

    user_voted = Boolean(help='Specifies if the user has voted on this problem or not.',
        scope=Scope.user_state, default=False)

    moderate = String(help='''If True, then all hints must be approved by staff before
        becoming visible.
        This field is automatically populated from the xml metadata.''', scope=Scope.content,
        default='False')

    mod_queue = Dict(help='''Contains hints that have not been approved by the staff yet.  Structured
        identically to the hints dictionary.''', scope=Scope.content, default={})

    hint_pk = Integer(help='Used to index hints.', scope=Scope.content, default=0)


class CrowdsourceHinterModule(CrowdsourceHinterFields, XModule):
    ''' An Xmodule that makes crowdsourced hints.
    '''
    icon_class = 'crowdsource_hinter'

    js = {'coffee': [resource_string(__name__, 'js/src/crowdsource_hinter/display.coffee'),
                 ],
      'js': []}
    js_module_name = "Hinter"


    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)


    def get_html(self):
        '''
        Does a regular expression find and replace to change the AJAX url.
        - Dependent on lon-capa problem.
        '''
        # Reset the user vote, for debugging only!  Remove for prod.
        self.user_voted = False
        # You are invited to guess what the lines below do :)
        if self.hints == {}:
            self.hints = {}

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
        return str(float(answer.values()[0]))


    def handle_ajax(self, dispatch, get):
        '''
        This is the landing method for AJAX calls.
        '''
        if dispatch == 'get_hint':
            out = self.get_hint(get)
        if dispatch == 'get_feedback':
            out = self.get_feedback(get)
        if dispatch == 'vote':
            out = self.tally_vote(get)
        if dispatch == 'submit_hint':
            out = self.submit_hint(get)

        if out == None:
            out = {'op': 'empty'}
        else:
            out.update({'op': dispatch})
        return json.dumps({'contents': self.system.render_template('hinter_display.html', out)})


    def get_hint(self, get):
        '''
        The student got the incorrect answer found in get.  Give him a hint.
        '''
        answer = self.ans_to_text(get)
        # Look for a hint to give.
        if (answer not in self.hints) or (len(self.hints[answer]) == 0):
            # No hints to give.  Return.
            self.previous_answers += [[answer, [None, None, None]]]
            return
        # Get the top hint, plus two random hints.
        n_hints = len(self.hints[answer])
        best_hint_index = max(self.hints[answer], key=lambda key: self.hints[answer][key][1])
        best_hint = self.hints[answer][best_hint_index][0]
        if len(self.hints[answer]) == 1:
            rand_hint_1 = ''
            rand_hint_2 = ''
            self.previous_answers += [[answer, [best_hint_index, None, None]]]
        elif n_hints == 2:
            best_hint = self.hints[answer].values()[0][0]
            best_hint_index = self.hints[answer].keys()[0]
            rand_hint_1 = self.hints[answer].values()[1][0]
            hint_index_1 = self.hints[answer].keys()[1]
            rand_hint_2 = ''
            self.previous_answers += [[answer, [best_hint_index, hint_index_1, None]]]
        else:
            (hint_index_1, rand_hint_1), (hint_index_2, rand_hint_2) =\
                random.sample(self.hints[answer].items(), 2)
            rand_hint_1 = rand_hint_1[0]
            rand_hint_2 = rand_hint_2[0]
            self.previous_answers += [(answer, (best_hint_index, hint_index_1, hint_index_2))]

        return {'best_hint': best_hint,
                'rand_hint_1': rand_hint_1, 
                'rand_hint_2': rand_hint_2, 
                'answer': answer}

    def get_feedback(self, get):
        '''
        The student got it correct.  Ask him to vote on hints, or submit a hint.
        '''
        # The student got it right.
        # Did he submit at least one wrong answer?
        out = ''
        if len(self.previous_answers) == 0:
            # No.  Nothing to do here.
            return
        # Make a hint-voting interface for each wrong answer.  The student will only
        # be allowed to make one vote / submission, but he can choose which wrong answer
        # he wants to look at.
        # index_to_hints[previous answer #] = [(hint text, hint pk), + ]
        index_to_hints = {}
        # index_to_answer[previous answer #] = answer text
        index_to_answer = {}

        for i in xrange(len(self.previous_answers)):
            answer, hints_offered = self.previous_answers[i]
            index_to_hints[i] = []
            index_to_answer[i] = answer
            if answer in self.hints:
                # Add each hint to the html string, with a vote button.
                for hint_id in hints_offered:
                    if hint_id != None:
                        try:
                            index_to_hints[i].append((self.hints[answer][hint_id][0], hint_id))
                        except KeyError:
                            # Sometimes, the hint that a user saw will have been deleted by the instructor.
                            continue

        return {'index_to_hints': index_to_hints, 'index_to_answer': index_to_answer}


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
        hint_no = str(get['hint'])
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
        return {'message': 'Congrats, you\'ve voted!'}


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
        if self.user_voted:
           return {'message': 'Sorry, but you have already voted!'}
        # Add the new hint to self.hints.  (Awkward because a direct write 
        # is necessary.)
        if self.moderate == 'True':
            temp_dict = self.mod_queue
        else:
            temp_dict = self.hints
        if answer in temp_dict:
            temp_dict[answer][self.hint_pk] = [hint, 1]     # With one vote (the user himself).
        else:
            temp_dict[answer] = {self.hint_pk: [hint, 1]}
        self.hint_pk += 1
        if self.moderate == 'True':
            self.mod_queue = temp_dict
        else:
            self.hints = temp_dict
        # Mark the user has having voted; reset previous_answers
        self.user_voted = True
        self.previous_answers = []
        return {'message': 'Thank you for your hint!'}


    def delete_hint(self, answer, hint_id):
        '''
        From the answer, delete the hint with hint_id.
        Not designed to be accessed via POST request, for now.
        -LIKELY DEPRECATED.
        '''
        temp_hints = self.hints
        del temp_hints[answer][str(hint_id)]
        self.hints = temp_hints


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