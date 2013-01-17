"""
A Self Assessment module that allows students to write open-ended responses,
submit, then see a rubric and rate themselves.  Persists student supplied
hints, answers, and assessment judgment (currently only correct/incorrect).
Parses xml definition file--see below for exact format.
"""

import copy
from fs.errors import ResourceNotFoundError
import itertools
import json
import logging
from lxml import etree
from lxml.html import rewrite_links
from path import path
import os
import sys

from pkg_resources import resource_string

from .capa_module import only_one, ComplexEncoder
from .editing_module import EditingDescriptor
from .html_checker import check_html
from progress import Progress
from .stringify import stringify_children
from .x_module import XModule
from .xml_module import XmlDescriptor
from xmodule.modulestore import Location

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

    STATE_VERSION = 1

    # states
    INITIAL = 'initial'
    ASSESSING = 'assessing'
    REQUEST_HINT = 'request_hint'
    DONE = 'done'

    js = {'coffee': [resource_string(__name__, 'js/src/selfassessment/display.coffee')]}
    js_module_name = "SelfAssessment"

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
            instance_state, shared_state, **kwargs)

        """
        Definition file should have 4 blocks -- prompt, rubric, submitmessage, hintprompt,
        and two optional attributes:
        attempts, which should be an integer that defaults to 1.
        If it's > 1, the student will be able to re-submit after they see
        the rubric.
        max_score, which should be an integer that defaults to 1.
        It defines the maximum number of points a student can get.  Assumed to be integer scale
        from 0 to max_score, with an interval of 1.

        Note: all the submissions are stored.

        Sample file:

        <selfassessment attempts="1" max_score="1">
            <prompt>
                Insert prompt text here.  (arbitrary html)
            </prompt>
            <rubric>
                Insert grading rubric here.  (arbitrary html)
            </rubric>
            <hintprompt>
                Please enter a hint below: (arbitrary html)
            </hintprompt>
            <submitmessage>
                Thanks for submitting!  (arbitrary html)
            </submitmessage>
        </selfassessment>
        """

        # Load instance state
        if instance_state is not None:
            instance_state = json.loads(instance_state)
        else:
            instance_state = {}

        instance_state = self.convert_state_to_current_format(instance_state)

        # History is a list of tuples of (answer, score, hint), where hint may be
        # None for any element, and score and hint can be None for the last (current)
        # element.
        # Scores are on scale from 0 to max_score
        self.history = instance_state.get('history', [])

        self.state = instance_state.get('state', 'initial')

        self.attempts = instance_state.get('attempts', 0)
        self.max_attempts = int(self.metadata.get('attempts', MAX_ATTEMPTS))

        # Used for progress / grading.  Currently get credit just for
        # completion (doesn't matter if you self-assessed correct/incorrect).
        self._max_score = int(self.metadata.get('max_score', MAX_SCORE))

        self.rubric = definition['rubric']
        self.prompt = definition['prompt']
        self.submit_message = definition['submitmessage']
        self.hint_prompt = definition['hintprompt']


    def latest_answer(self):
        """None if not available"""
        if not self.history:
            return None
        return self.history[-1].get('answer')

    def latest_score(self):
        """None if not available"""
        if not self.history:
            return None
        return self.history[-1].get('score')

    def latest_hint(self):
        """None if not available"""
        if not self.history:
            return None
        return self.history[-1].get('hint')

    def new_history_entry(self, answer):
        self.history.append({'answer': answer})

    def record_latest_score(self, score):
        """Assumes that state is right, so we're adding a score to the latest
        history element"""
        self.history[-1]['score'] = score

    def record_latest_hint(self, hint):
        """Assumes that state is right, so we're adding a score to the latest
        history element"""
        self.history[-1]['hint'] = hint


    def change_state(self, new_state):
        """
        A centralized place for state changes--allows for hooks.  If the
        current state matches the old state, don't run any hooks.
        """
        if self.state == new_state:
            return

        self.state = new_state

        if self.state == self.DONE:
            self.attempts += 1

    @staticmethod
    def convert_state_to_current_format(old_state):
        """
        This module used to use a problematic state representation. This method
        converts that into the new format.

        Args:
            old_state: dict of state, as passed in.  May be old.

        Returns:
            new_state: dict of new state
        """
        if old_state.get('version', 0) == SelfAssessmentModule.STATE_VERSION:
            # already current
            return old_state

        # for now, there's only one older format.

        new_state = {'version': SelfAssessmentModule.STATE_VERSION}

        def copy_if_present(key):
            if key in old_state:
                new_state[key] = old_state[key]

        for to_copy in ['attempts', 'state']:
            copy_if_present(to_copy)

        # The answers, scores, and hints need to be kept together to avoid them
        # getting out of sync.

        # NOTE: Since there's only one problem with a few hundred submissions
        # in production so far, not trying to be smart about matching up hints
        # and submissions in cases where they got out of sync.

        student_answers = old_state.get('student_answers', [])
        scores = old_state.get('scores', [])
        hints = old_state.get('hints', [])

        new_state['history'] = [
            {'answer': answer,
             'score': score,
             'hint': hint}
             for answer, score, hint in itertools.izip_longest(
                     student_answers, scores, hints)]
        return new_state


    def _allow_reset(self):
        """Can the module be reset?"""
        return self.state == self.DONE and self.attempts < self.max_attempts

    def get_html(self):
        #set context variables and render template
        if self.state != self.INITIAL:
            latest = self.latest_answer()
            previous_answer = latest if latest is not None else ''
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

    def max_score(self):
        """
        Return max_score
        """
        return self._max_score

    def get_score(self):
        """
        Returns the last score in the list
        """
        score = self.latest_score()
        return {'score': score if score is not None else 0,
                'total': self._max_score}

    def get_progress(self):
        '''
        For now, just return last score / max_score
        '''
        if self._max_score > 0:
            try:
                return Progress(self.get_score()['score'], self._max_score)
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

        if self.state == self.DONE:
            # display the previous hint
            latest = self.latest_hint()
            hint = latest if latest is not None else ''
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

        Args:
            get: the GET dictionary passed to the ajax request.  Should contain
                a key 'student_answer'

        Returns:
            Dictionary with keys 'success' and either 'error' (if not success),
            or 'rubric_html' (if success).
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

        # add new history element with answer and empty score and hint.
        self.new_history_entry(get['student_answer'])
        self.change_state(self.ASSESSING)

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

        if self.state != self.ASSESSING:
            return self.out_of_sync_error(get)

        try:
            score = int(get['assessment'])
        except ValueError:
            return {'success': False, 'error': "Non-integer score value"}

        self.record_latest_score(score)

        d = {'success': True,}

        if score == self.max_score():
            self.change_state(self.DONE)
            d['message_html'] = self.get_message_html()
            d['allow_reset'] = self._allow_reset()
        else:
            self.change_state(self.REQUEST_HINT)
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

        self.record_latest_hint(get['hint'])
        self.change_state(self.DONE)

        # To the tracking logs!
        event_info = {
            'selfassessment_id': self.location.url(),
            'state': {
                'version': self.STATE_VERSION,
                'history': self.history,
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
        self.change_state(self.INITIAL)
        return {'success': True}


    def get_instance_state(self):
        """
        Get the current score and state
        """

        state = {
                 'version': self.STATE_VERSION,
                 'history': self.history,
                 'state': self.state,
                 'max_score': self._max_score,
                 'attempts': self.attempts,
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
    css = {'scss': [resource_string(__name__, 'css/editor/edit.scss'), resource_string(__name__, 'css/html/edit.scss')]}

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
                }


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
