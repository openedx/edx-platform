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
import self_assessment_module
import open_ended_module

log = logging.getLogger("mitx.courseware")

# Set the default number of max attempts.  Should be 1 for production
# Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 10000

# Set maximum available number of points.
# Overriden by max_score specified in xml.
MAX_SCORE = 1

class CombinedOpenEndedModule(XModule):
    STATE_VERSION = 1

    # states
    INITIAL = 'initial'
    ASSESSING = 'assessing'
    INTERMEDIATE_DONE='intermediate_done'
    DONE = 'done'
    TASK_TYPES=["self", "ml", "instructor", "peer"]

    js = {'coffee': [resource_string(__name__, 'js/src/combinedopenended/display.coffee')]}
    js_module_name = "CombinedOpenEnded"

    css = {'scss': [resource_string(__name__, 'css/combinedopenended/display.scss')]}

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
            instance_state, shared_state, **kwargs)

        """
        Definition file should have multiple task blocks:

        Sample file:

        <combinedopenended max_score="1" attempts="1">
            <task type="self">
                <selfassessment>
                </selfassessment>
            </task>
        </combinedopenended>
        """

        # Load instance state
        if instance_state is not None:
            instance_state = json.loads(instance_state)
        else:
            instance_state = {}

        # History is a list of tuples of (answer, score, hint), where hint may be
        # None for any element, and score and hint can be None for the last (current)
        # element.
        # Scores are on scale from 0 to max_score
        system.set('location', location)
        log.debug(system.location)
        self.current_task_number = instance_state.get('current_task_number', 0)
        self.task_states= instance_state.get('task_states', [])

        self.state = instance_state.get('state', 'initial')

        self.attempts = instance_state.get('attempts', 0)
        self.max_attempts = int(self.metadata.get('attempts', MAX_ATTEMPTS))

        # Used for progress / grading.  Currently get credit just for
        # completion (doesn't matter if you self-assessed correct/incorrect).
        self._max_score = int(self.metadata.get('max_score', MAX_SCORE))

        self.task_xml=definition['task_xml']
        self.setup_next_task()

    def get_tag_name(self, xml):
        tag=etree.fromstring(xml).tag
        return tag

    def overwrite_state(self, current_task_state):
        last_response_data=self.get_last_response(self.current_task_number-1)
        last_response = last_response_data['response']

        loaded_task_state=json.loads(current_task_state)
        if loaded_task_state['state']== self.INITIAL:
            loaded_task_state['state']=self.ASSESSING
            loaded_task_state['created'] = "True"
            loaded_task_state['history'].append({'answer' : last_response})
            current_task_state=json.dumps(loaded_task_state)
        return current_task_state

    def child_modules(self):
        child_modules={
            'openended' : open_ended_module.OpenEndedModule,
            'selfassessment' : self_assessment_module.SelfAssessmentModule,
        }
        child_descriptors={
            'openended' : open_ended_module.OpenEndedDescriptor,
            'selfassessment' : self_assessment_module.SelfAssessmentDescriptor,
        }
        children={
            'modules' : child_modules,
            'descriptors' : child_descriptors,
        }
        return children

    def setup_next_task(self, reset=False):
        current_task_state=None
        if len(self.task_states)>self.current_task_number:
            current_task_state=self.task_states[self.current_task_number]

        self.current_task_xml=self.task_xml[self.current_task_number]
        current_task_type=self.get_tag_name(self.current_task_xml)

        children=self.child_modules()

        self.current_task_descriptor=children['descriptors'][current_task_type](self.system)
        self.current_task_parsed_xml=self.current_task_descriptor.definition_from_xml(etree.fromstring(self.current_task_xml),self.system)
        if current_task_state is None and self.current_task_number==0:
            self.current_task=children['modules'][current_task_type](self.system, self.location, self.current_task_parsed_xml, self.current_task_descriptor)
            self.task_states.append(self.current_task.get_instance_state())
            self.state=self.ASSESSING
        elif current_task_state is None and self.current_task_number>0:
            last_response_data =self.get_last_response(self.current_task_number-1)
            last_response = last_response_data['response']
            current_task_state = ('{"state": "assessing", "version": 1, "max_score": ' + str(self._max_score) + ', ' +
                                  '"attempts": 0, "created": "True", "history": [{"answer": "' + str(last_response) + '"}]}')
            self.current_task=children['modules'][current_task_type](self.system, self.location, self.current_task_parsed_xml, self.current_task_descriptor, instance_state=current_task_state)
            self.task_states.append(self.current_task.get_instance_state())
            self.state=self.ASSESSING
        else:
            if self.current_task_number>0 and not reset:
                current_task_state=self.overwrite_state(current_task_state)
            self.current_task=children['modules'][current_task_type](self.system, self.location, self.current_task_parsed_xml, self.current_task_descriptor, instance_state=current_task_state)

        log.debug(self.current_task.get_instance_state())
        log.debug(self.get_instance_state())
        return True

    def get_html(self):
        task_html=self.get_html_base()
        #set context variables and render template

        context = {
            'items': [{'content' : task_html}],
            'ajax_url': self.system.ajax_url,
            'allow_reset': True,
            'state' : self.state,
            'task_count' : len(self.task_xml),
            'task_number' : self.current_task_number+1,
            'status' : self.get_status(),
            }

        html = self.system.render_template('combined_open_ended.html', context)
        return html


    def get_html_base(self):
        self.update_task_states()
        html = self.current_task.get_html(self.system)
        return_html = rewrite_links(html, self.rewrite_content_links)
        return return_html

    def get_last_response(self, task_number):
        last_response=""
        task_state = self.task_states[task_number]
        task_xml=self.task_xml[task_number]
        task_type=self.get_tag_name(task_xml)

        children=self.child_modules()

        task_descriptor=children['descriptors'][task_type](self.system)
        task_parsed_xml=task_descriptor.definition_from_xml(etree.fromstring(task_xml),self.system)
        task=children['modules'][task_type](self.system, self.location, task_parsed_xml, task_descriptor, instance_state=task_state)
        last_response=task.latest_answer()
        last_score = task.latest_score()
        last_post_assessment = task.latest_post_assessment()
        max_score = task.max_score()
        last_response_dict={'response' : last_response, 'score' : last_score, 'post_assessment' : last_post_assessment, 'type' : task_type, 'max_score' : max_score}

        return last_response_dict

    def update_task_states(self):
        changed=False
        self.task_states[self.current_task_number] = self.current_task.get_instance_state()
        current_task_state=json.loads(self.task_states[self.current_task_number])
        if current_task_state['state']==self.DONE:
            self.current_task_number+=1
            if self.current_task_number>=(len(self.task_xml)):
                self.state=self.DONE
                self.current_task_number=len(self.task_xml)-1
            else:
                self.state=self.INITIAL
            changed=True
            self.setup_next_task()
        return changed

    def update_task_states_ajax(self,return_html):
        changed=self.update_task_states()
        if changed:
            #return_html=self.get_html()
            pass
        return return_html

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
            'next_problem': self.next_problem,
            'reset': self.reset,
            }

        if dispatch not in handlers:
            return_html = self.current_task.handle_ajax(dispatch,get, self.system)
            return self.update_task_states_ajax(return_html)

        d = handlers[dispatch](get)
        return json.dumps(d,cls=ComplexEncoder)

    def next_problem(self, get):
        self.update_task_states()
        return {'success' : True}

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
        self.state=self.INITIAL
        for i in xrange(0,len(self.task_xml)):
            self.current_task_number=i
            self.setup_next_task(reset=True)
            self.current_task.reset(self.system)
            self.task_states[self.current_task_number]=self.current_task.get_instance_state()
        self.current_task_number=0
        self.setup_next_task()
        return {'success': True}

    def get_instance_state(self):
        """
        Get the current score and state
        """

        state = {
            'version': self.STATE_VERSION,
            'current_task_number': self.current_task_number,
            'state': self.state,
            'task_states': self.task_states,
            'attempts': self.attempts,
            }

        return json.dumps(state)

    def get_status(self):
        status=[]
        for i in xrange(0,self.current_task_number):
            task_data = self.get_last_response(i)
            task_data.update({'task_number' : i+1})
            status.append(task_data)
        context = {'status_list' : status}
        status_html = self.system.render_template("combined_open_ended_status.html", context)

        return status_html

class CombinedOpenEndedDescriptor(XmlDescriptor, EditingDescriptor):
    """
    Module for adding self assessment questions to courses
    """
    mako_template = "widgets/html-edit.html"
    module_class = CombinedOpenEndedModule
    filename_extension = "xml"

    stores_state = True
    has_score = True
    template_dir_name = "combinedopenended"

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
        expected_children = ['task']
        for child in expected_children:
            if len(xml_object.xpath(child)) == 0 :
                raise ValueError("Combined Open Ended definition must include at least one '{0}' tag".format(child))

        def parse(k):
            """Assumes that xml_object has child k"""
            return [stringify_children(xml_object.xpath(k)[i]) for i in xrange(0,len(xml_object.xpath(k)))]

        return {'task_xml': parse('task')}


    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        elt = etree.Element('combinedopenended')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in ['task']:
            add_child(child)

        return elt