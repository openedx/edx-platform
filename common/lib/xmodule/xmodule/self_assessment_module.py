"""
Add Self Assessment module so students can write essay, submit, then see a rubric and rate themselves.
Incredibly hacky solution to persist state and properly display information
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
from .xml_module import XmlDescriptor, name_to_pathname
from xmodule.modulestore import Location

from xmodule.contentstore.content import XASSET_SRCREF_PREFIX, StaticContent

log = logging.getLogger("mitx.courseware")

#Set the default number of max attempts.  Should be 1 for production
#Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 1

#Set maximum available number of points.  Should be set to 1 for now due to correctness handling,
# which only allows for correct/incorrect.
MAX_SCORE=1

class SelfAssessmentModule(XModule):
    js = {'coffee': [resource_string(__name__, 'js/src/selfassessment/display.coffee')]
    }
    js_module_name = "SelfAssessment"

    def get_html(self):
        # cdodge: perform link substitutions for any references to course static content (e.g. images)
        return rewrite_links(self.html, self.rewrite_content_links)

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
            instance_state, shared_state, **kwargs)

        """
        Definition file should have 3 blocks -- prompt, rubric, submitmessage, and one optional attribute, attempts,
        which should be an integer that defaults to 1.  If it's >1, the student will be able to re-submit after they see
        the rubric.  Note: all the submissions are stored.

        Sample file:

        <selfassessment attempts="1">
            <prompt>
                Insert prompt text here.  (arbitrary html)
            </prompt>
            <rubric>
                Insert grading rubric here.  (arbitrary html)
            </rubric>
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

        log.debug('Instance state of self-assessment module {0}: {1}'.format(location.url(), instance_state))

        # Pull out state, or initialize variables

        # lists of student answers, correctness responses ('incorrect'/'correct'), and suggested hints
        self.student_answers = instance_state.get('student_answers', [])
        self.correctness = instance_state.get('correctness', [])
        self.hints = instance_state.get('hints', [])

        # Used to keep track of a submitted answer for which we don't have a self-assessment and hint yet:
        # this means that the answers, correctness, hints always stay in sync, and have the same number of elements.
        self.temp_answer = instance_state.get('temp_answer', '')

        # Used for progress / grading.  Currently get credit just for completion (doesn't matter if you self-assessed
        # correct/incorrect).
        self.score = instance_state.get('score', 0)
        self.top_score = instance_state.get('top_score', MAX_SCORE)

        # TODO: do we need this?  True once everything is done
        self.done = instance_state.get('done', False)

        self.attempts = instance_state.get('attempts', 0)

        #Try setting maxattempts, use default if not available in metadata
        self.max_attempts = int(self.metadata.get('attempts', MAX_ATTEMPTS))

        #Extract prompt, submission message and rubric from definition file
        self.rubric = definition['rubric']
        self.prompt = definition['prompt']
        self.submit_message = definition['submitmessage']

        #set context variables and render template
        previous_answer=''
        if len(self.student_answers)>0:
            previous_answer=self.student_answers[len(self.student_answers)-1]

        self.context = {
            'prompt' : self.prompt,
            'rubric' : self.rubric,
            'previous_answer_given' : len(self.student_answers)>0,
            'previous_answer' : previous_answer,
            'ajax_url' : system.ajax_url,
            'section_name' : 'sa-wrapper',
        }
        self.html = self.system.render_template('self_assessment_prompt.html', self.context)

    def get_score(self):
        return {'score': self.score}

    def max_score(self):
        return self.top_score

    def get_progress(self):
        ''' For now, just return score / max_score
        '''
        score = self.score
        total = self.top_score
        if total > 0:
            try:
                return Progress(score, total)
            except Exception as err:
                log.exception("Got bad progress")
                return None
        return None


    def handle_ajax(self, dispatch, get):
        '''
        This is called by courseware.module_render, to handle an AJAX call.
        "get" is request.POST.

        Returns a json dictionary:
        { 'progress_changed' : True/False,
        'progress' : 'none'/'in_progress'/'done',
        <other request-specific values here > }
        '''

        handlers = {
            'sa_show': self.show_rubric,
            'sa_save': self.save_problem,
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

    def show_rubric(self, get):
        """
        After the prompt is submitted, show the rubric
        """
        #Check to see if attempts are less than max
        if(self.attempts < self.max_attempts):
            # Dump to temp to keep answer in sync with correctness and hint

            # TODO: expecting something like get['answer']
            self.temp_answer = get['student_answer']
            log.debug(self.temp_answer)
            return {
                'success': True,
                'rubric': self.system.render_template('self_assessment_rubric.html', self.context)
            }
        else:
            return{
                'success': False,
                'message': 'Too many attempts.'
            }

    def save_problem(self, get):
        '''
        Save the passed in answers.
        Returns a dict { 'success' : bool, ['error' : error-msg]},
        with the error key only present if success is False.
        '''

        #Temp answer check is to keep hints, correctness, and answer in sync
        points = 0
        log.debug(self.temp_answer)
        if self.temp_answer is not "":
            #Extract correctness and hint from ajax and assign points
            self.hints.append(get['hint'])
            curr_correctness = get['assessment'].lower()
            if curr_correctness == "correct":
                points = 1
            self.correctness.append(curr_correctness)
            self.student_answers.append(self.temp_answer)

        #Student is done, and increment attempts
        self.done = True
        self.attempts = self.attempts + 1

        # TODO: simplify tracking info to just log the relevant stuff
        event_info = dict()
        event_info['state'] = {
                               'student_answers': self.student_answers,
                               'hint' : self.hints,
                               'correctness': self.correctness,
                               'score': points,
                               'done': self.done
        }

        # TODO: figure out how to identify self assessment.  May not want to confuse with problems.
        event_info['selfassessment_id'] = self.location.url()

        self.system.track_function('save_problem_succeed', event_info)

        return {'success': True, 'message': self.submit_message}

    def get_instance_state(self):
        """
        Get the current correctness, points, and done status
        """
        #Assign points based on completion
        points = 1
        #This is a pointless if structure, but left in place in case points change from
        #being completion based to correctness based

        # TODO: clean up
        if type(self.correctness)==type([]):
            if(len(self.correctness)>0):
                if self.correctness[len(self.correctness)-1]== "correct":
                    points = 1

        state = {
                 'student_answers': self.student_answers,
                 'temp_answer': self.temp_answer,
                 'hint' : self.hints,
                 'correctness': self.correctness,
                 'score': points,
                 'top_score' : MAX_SCORE,
                 'done': self.done,
                 'attempts' : self.attempts
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
        'rubric' : 'some-html',
        'prompt' : 'some-html',
        'submitmessage' : 'some-html'
        }
        """
        expected_children = ['rubric', 'prompt', 'submitmessage']
        for child in expected_children:
            if len(xml_object.xpath(child)) != 1:
                raise ValueError("Self assessment definition must include exactly one '{0}' tag".format(child))

        def parse(k):
            """Assumes that xml_object has child k"""
            return stringify_children(xml_object.xpath(k)[0])

        return {'rubric' : parse('rubric'),
                'prompt' : parse('prompt'),
                'submitmessage' : parse('submitmessage'),}


    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        elt = etree.Element('selfassessment')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in ['rubric', 'prompt', 'submitmessage']:
            add_child(child)

        return elt
