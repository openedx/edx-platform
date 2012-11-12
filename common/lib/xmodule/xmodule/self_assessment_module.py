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

log = logging.getLogger("mitx.courseware")

# Set the default number of max attempts.  Should be 1 for production
# Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 1

# Set maximum available number of points.  Should be set to 1 for now due to assessment handling,
# which only allows for correct/incorrect.
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

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
            instance_state, shared_state, **kwargs)

        """
        Definition file should have 4 blocks -- prompt, rubric, submitmessage, hintprompt,
        and one optional attribute, attempts, which should be an integer that defaults to 1.
        If it's > 1, the student will be able to re-submit after they see
        the rubric.  Note: all the submissions are stored.

        Sample file:

        <selfassessment attempts="1">
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

        # Note: assessment responses are 'incorrect'/'correct'
        self.student_answers = instance_state.get('student_answers', [])
        self.assessment = instance_state.get('assessment', [])
        self.hints = instance_state.get('hints', [])

        self.state = instance_state.get('state', 'initial')

        # Used for progress / grading.  Currently get credit just for
        # completion (doesn't matter if you self-assessed correct/incorrect).
        self.score = instance_state.get('score', 0)
        self._max_score = instance_state.get('max_score', MAX_SCORE)

        self.attempts = instance_state.get('attempts', 0)

        self.max_attempts = int(self.metadata.get('attempts', MAX_ATTEMPTS))

        self.rubric = definition['rubric']
        self.prompt = definition['prompt']
        self.submit_message = definition['submitmessage']
        self.hint_prompt = definition['hintprompt']

    def get_html(self):
        #set context variables and render template
        previous_answer = self.student_answers[-1] if self.student_answers else ''

        allow_reset = self.state == self.DONE and self.attempts < self.max_attempts
        context = {
            'prompt': self.prompt,
            'previous_answer': previous_answer,
            'ajax_url': self.system.ajax_url,
            'initial_rubric': self.get_rubric_html(),
            'initial_hint': self.get_hint_html(),
            'initial_message': self.get_message_html(),
            'state': self.state,
            'allow_reset': allow_reset,
        }
        html = self.system.render_template('self_assessment_prompt.html', context)

        # cdodge: perform link substitutions for any references to course static content (e.g. images)
        return rewrite_links(html, self.rewrite_content_links)

    def get_score(self):
        """
        Returns dict with 'score' key
        """
        return {'score': self.score}

    def max_score(self):
        """
        Return max_score
        """
        return self._max_score

    def get_progress(self):
        '''
        For now, just return score / max_score
        '''
        if self._max_score > 0:
            try:
                return Progress(self.score, self._max_score)
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

    def out_of_sync_error(self, get):
        """
        return dict out-of-sync error message, and also log.
        """
        log.warning("Assessment module state out sync. state: %r, get: %r",
                    self.state, get)
        return {'success': False,
                'error': 'The problem state got out-of-sync'}

    def get_rubric_html(self):
        """
        Return the appropriate version of the rubric, based on the state.
        """
        if self.state == self.INITIAL:
            return ''

        # we'll render it
        context = {'rubric': self.rubric}

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

        # else we'll render it
        hint = self.hints[-1] if len(self.hints) > 0 else ''
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
                'message': 'Too many attempts.'
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
        Save the assessment.

        Returns a dict { 'success': bool, 'hint_html': hint_html 'error': error-msg},
        with 'error' only present if 'success' is False, and 'hint_html' only if success is true
        """

        if (self.state != self.ASSESSING or
            len(self.student_answers) !=  len(self.assessment) + 1):
            return self.out_of_sync_error(get)

        self.assessment.append(get['assessment'].lower())
        self.state = self.REQUEST_HINT

        # TODO: return different hint based on assessment value...
        return {'success': True, 'hint_html': self.get_hint_html()}

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
        if self.state != self.REQUEST_HINT or len(self.assessment) !=  len(self.hints) + 1:
            return self.out_of_sync_error(get)

        self.hints.append(get['hint'].lower())
        self.state = self.DONE

        # Points are assigned for completion, so always set to 1
        points = 1
        # increment attempts
        self.attempts = self.attempts + 1

        # To the tracking logs!
        event_info = {
            'selfassessment_id': self.location.url(),
            'state': {
                'student_answers': self.student_answers,
                'assessment': self.assessment,
                'hints': self.hints,
                'score': points,
                }
            }
        self.system.track_function('save_hint', event_info)

        return {'success': True,
                'message_html': self.get_message_html(),
                'allow_reset': self.attempts < self.max_attempts}


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
        Get the current assessment, points, and state
        """
        #Assign points based on completion.  May want to change to assessment-based down the road.
        points = 1

        state = {
                 'student_answers': self.student_answers,
                 'assessment': self.assessment,
                 'hints': self.hints,
                 'state': self.state,
                 'score': points,
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
