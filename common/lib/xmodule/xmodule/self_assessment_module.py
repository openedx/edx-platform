"""
A Self Assessment module that allows students to write open-ended responses,
submit, then see a rubric and rate themselves.  Persists student supplied
hints, answers, and assessment judgment (currently only correct/incorrect).
Parses xml definition file--see below for exact format.
"""

import copy
from fs.errors import ResourceNotFoundError
import logging
import os
import sys
from lxml import etree
from lxml.html import rewrite_links
from path import path
import json
from progress import Progress

from pkg_resources import resource_string

from .capa_module import only_one, ComplexEncoder
from .editing_module import EditingDescriptor
from .html_checker import check_html
from .stringify import stringify_children
from .x_module import XModule
from .xml_module import XmlDescriptor
from xmodule.modulestore import Location
from .model import List, String, Scope, Int

log = logging.getLogger("mitx.courseware")

# Set the default number of max attempts.  Should be 1 for production
# Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 1

# Set maximum available number of points.
# Overriden by max_score specified in xml.
MAX_SCORE = 1

class SelfAssessmentModule(XModule):
    """
    States:

    initial (prompt, textbox shown)
         |
    assessing (read-only textbox, rubric + assessment input shown)
         |
    request_hint (read-only textbox, read-only rubric and assessment, hint input box shown)
         |
    done (submitted msg, green checkmark, everything else read-only.  If attempts < max, shows
         a reset button that goes back to initial state.  Saves previous
         submissions too.)
    """

    # states
    INITIAL = 'initial'
    ASSESSING = 'assessing'
    REQUEST_HINT = 'request_hint'
    DONE = 'done'

    js = {'coffee': [resource_string(__name__, 'js/src/selfassessment/display.coffee')]}
    js_module_name = "SelfAssessment"

    student_answers = List(scope=Scope.student_state, default=[])
    scores = List(scope=Scope.student_state, default=[])
    hints = List(scope=Scope.student_state, default=[])
    state = String(scope=Scope.student_state, default=INITIAL)

    # Used for progress / grading.  Currently get credit just for
    # completion (doesn't matter if you self-assessed correct/incorrect).
    max_score = Int(scope=Scope.settings, default=MAX_SCORE)

    attempts = Int(scope=Scope.student_state, default=0), Int
    max_attempts = Int(scope=Scope.settings, default=MAX_ATTEMPTS)
    rubric = String(scope=Scope.content)
    prompt = String(scope=Scope.content)
    submit_message = String(scope=Scope.content)
    hint_prompt = String(scope=Scope.content)

    def _allow_reset(self):
        """Can the module be reset?"""
        return self.state == self.DONE and self.attempts < self.max_attempts

    def get_html(self):
        #set context variables and render template
        if self.state != self.INITIAL and self.student_answers:
            previous_answer = self.student_answers[-1]
        else:
            previous_answer = ''

        context = {
            'prompt': self.prompt,
            'previous_answer': previous_answer,
            'ajax_url': self.system.ajax_url,
            'initial_rubric': self.get_rubric_html(),
            'initial_hint': self.get_hint_html(),
            'initial_message': self.get_message_html(),
            'state': self.state,
            'allow_reset': self._allow_reset(),
        }
        html = self.system.render_template('self_assessment_prompt.html', context)

        # cdodge: perform link substitutions for any references to course static content (e.g. images)
        return rewrite_links(html, self.rewrite_content_links)

    def get_score(self):
        """
        Returns dict with 'score' key
        """
        return {'score': self.get_last_score()}

    def max_score(self):
        """
        Return max_score
        """
        return self._max_score

    def get_last_score(self):
        """
        Returns the last score in the list
        """
        last_score=0
        if(len(self.scores)>0):
            last_score=self.scores[len(self.scores)-1]
        return last_score

    def get_progress(self):
        '''
        For now, just return last score / max_score
        '''
        if self._max_score > 0:
            try:
                return Progress(self.get_last_score(), self._max_score)
            except Exception as err:
                log.exception("Got bad progress")
                return None
        return None


    def handle_ajax(self, dispatch, get):
        """
        This is called by courseware.module_render, to handle an AJAX call.
        "get" is request.POST.

        Returns a json dictionary:
        { 'progress_changed' : True/False,
        'progress': 'none'/'in_progress'/'done',
        <other request-specific values here > }
        """

        handlers = {
            'save_answer': self.save_answer,
            'save_assessment': self.save_assessment,
            'save_hint': self.save_hint,
            'reset': self.reset,
        }

        if dispatch not in handlers:
            return 'Error'

        before = self.get_progress()
        d = handlers[dispatch](get)
        after = self.get_progress()
        d.update({
            'progress_changed': after != before,
            'progress_status': Progress.to_js_status_str(after),
        })
        return json.dumps(d, cls=ComplexEncoder)

    def out_of_sync_error(self, get, msg=''):
        """
        return dict out-of-sync error message, and also log.
        """
        log.warning("Assessment module state out sync. state: %r, get: %r. %s",
                    self.state, get, msg)
        return {'success': False,
                'error': 'The problem state got out-of-sync'}

    def get_rubric_html(self):
        """
        Return the appropriate version of the rubric, based on the state.
        """
        if self.state == self.INITIAL:
            return ''

        # we'll render it
        context = {'rubric': self.rubric,
                   'max_score' : self._max_score,
                   }

        if self.state == self.ASSESSING:
            context['read_only'] = False
        elif self.state in (self.REQUEST_HINT, self.DONE):
            context['read_only'] = True
        else:
            raise ValueError("Illegal state '%r'" % self.state)

        return self.system.render_template('self_assessment_rubric.html', context)

    def get_hint_html(self):
        """
        Return the appropriate version of the hint view, based on state.
        """
        if self.state in (self.INITIAL, self.ASSESSING):
            return ''

        if self.state == self.DONE and len(self.hints) > 0:
            # display the previous hint
            hint = self.hints[-1]
        else:
            hint = ''

        context = {'hint_prompt': self.hint_prompt,
                   'hint': hint}

        if self.state == self.REQUEST_HINT:
            context['read_only'] = False
        elif self.state == self.DONE:
            context['read_only'] = True
        else:
            raise ValueError("Illegal state '%r'" % self.state)

        return self.system.render_template('self_assessment_hint.html', context)

    def get_message_html(self):
        """
        Return the appropriate version of the message view, based on state.
        """
        if self.state != self.DONE:
            return ""

        return """<div class="save_message">{0}</div>""".format(self.submit_message)


    def save_answer(self, get):
        """
        After the answer is submitted, show the rubric.
        """
        # Check to see if attempts are less than max
        if self.attempts > self.max_attempts:
            # If too many attempts, prevent student from saving answer and
            # seeing rubric.  In normal use, students shouldn't see this because
            # they won't see the reset button once they're out of attempts.
            return {
                'success': False,
                'error': 'Too many attempts.'
            }

        if self.state != self.INITIAL:
            return self.out_of_sync_error(get)

        self.student_answers.append(get['student_answer'])
        self.state = self.ASSESSING

        return {
            'success': True,
            'rubric_html': self.get_rubric_html()
            }

    def save_assessment(self, get):
        """
        Save the assessment.  If the student said they're right, don't ask for a
        hint, and go straight to the done state.  Otherwise, do ask for a hint.

        Returns a dict { 'success': bool, 'state': state,

        'hint_html': hint_html OR 'message_html': html and 'allow_reset',

           'error': error-msg},

        with 'error' only present if 'success' is False, and 'hint_html' or
        'message_html' only if success is true
        """

        n_answers = len(self.student_answers)
        n_scores = len(self.scores)
        if (self.state != self.ASSESSING or n_answers !=  n_scores + 1):
            msg = "%d answers, %d scores" % (n_answers, n_scores)
            return self.out_of_sync_error(get, msg)

        try:
            score = int(get['assessment'])
        except:
            return {'success': False, 'error': "Non-integer score value"}

        self.scores.append(score)

        d = {'success': True,}

        if score == self.max_score():
            self.state = self.DONE
            d['message_html'] = self.get_message_html()
            d['allow_reset'] = self._allow_reset()
        else:
            self.state = self.REQUEST_HINT
            d['hint_html'] = self.get_hint_html()

        d['state'] = self.state
        return d


    def save_hint(self, get):
        '''
        Save the hint.
        Returns a dict { 'success': bool,
                         'message_html': message_html,
                         'error': error-msg,
                         'allow_reset': bool},
        with the error key only present if success is False and message_html
        only if True.
        '''
        if self.state != self.REQUEST_HINT:
            # Note: because we only ask for hints on wrong answers, may not have
            # the same number of hints and answers.
            return self.out_of_sync_error(get)

        self.hints.append(get['hint'].lower())
        self.state = self.DONE

        # increment attempts
        self.attempts = self.attempts + 1

        # To the tracking logs!
        event_info = {
            'selfassessment_id': self.location.url(),
            'state': {
                'student_answers': self.student_answers,
                'score': self.scores,
                'hints': self.hints,
                }
            }
        self.system.track_function('save_hint', event_info)

        return {'success': True,
                'message_html': self.get_message_html(),
                'allow_reset': self._allow_reset()}


    def reset(self, get):
        """
        If resetting is allowed, reset the state.

        Returns {'success': bool, 'error': msg}
        (error only present if not success)
        """
        if self.state != self.DONE:
            return self.out_of_sync_error(get)

        if self.attempts > self.max_attempts:
            return {
                'success': False,
                'error': 'Too many attempts.'
            }
        self.state = self.INITIAL
        return {'success': True}


    def get_instance_state(self):
        """
        Get the current score and state
        """

        state = {
                 'student_answers': self.student_answers,
                 'hints': self.hints,
                 'state': self.state,
                 'scores': self.scores,
                 'max_score': self._max_score,
                 'attempts': self.attempts
        }
        return json.dumps(state)


class SelfAssessmentDescriptor(XmlDescriptor, EditingDescriptor):
    """
    Module for adding self assessment questions to courses
    """
    mako_template = "widgets/html-edit.html"
    module_class = SelfAssessmentModule
    filename_extension = "xml"

    stores_state = True
    has_score = True
    template_dir_name = "selfassessment"

    js = {'coffee': [resource_string(__name__, 'js/src/html/edit.coffee')]}
    js_module_name = "HTMLEditingDescriptor"

    # The capa format specifies that what we call max_attempts in the code
    # is the attribute `attempts`. This will do that conversion
    metadata_translations = dict(XmlDescriptor.metadata_translations)
    metadata_translations['attempts'] = 'max_attempts'

    # Used for progress / grading.  Currently get credit just for
    # completion (doesn't matter if you self-assessed correct/incorrect).
    max_score = Int(scope=Scope.settings, default=MAX_SCORE)

    max_attempts = Int(scope=Scope.settings, default=MAX_ATTEMPTS)
    rubric = String(scope=Scope.content)
    prompt = String(scope=Scope.content)
    submit_message = String(scope=Scope.content)
    hint_prompt = String(scope=Scope.content)

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Pull out the rubric, prompt, and submitmessage into a dictionary.

        Returns:
        {
        'rubric': 'some-html',
        'prompt': 'some-html',
        'submitmessage': 'some-html'
        'hintprompt': 'some-html'
        }
        """
        expected_children = ['rubric', 'prompt', 'submitmessage', 'hintprompt']
        for child in expected_children:
            if len(xml_object.xpath(child)) != 1:
                raise ValueError("Self assessment definition must include exactly one '{0}' tag".format(child))

        def parse(k):
            """Assumes that xml_object has child k"""
            return stringify_children(xml_object.xpath(k)[0])

        return {'rubric': parse('rubric'),
                'prompt': parse('prompt'),
                'submitmessage': parse('submitmessage'),
                'hintprompt': parse('hintprompt'),
                }, []


    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        elt = etree.Element('selfassessment')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in ['rubric', 'prompt', 'submitmessage', 'hintprompt']:
            add_child(child)

        return elt
