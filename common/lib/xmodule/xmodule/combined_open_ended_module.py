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

log = logging.getLogger("mitx.courseware")

# Set the default number of max attempts.  Should be 1 for production
# Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 1

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

    js = {'coffee': [resource_string(__name__, 'js/src/selfassessment/display.coffee')]}
    js_module_name = "CombinedOpenEnded"

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
        self.current_task_number = instance_state.get('current_task_number', 0)
        self.tasks = instance_state.get('tasks', [])

        self.state = instance_state.get('state', 'initial')
        self.problems = instance_state.get('problems', [])

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

    def setup_next_task(self):
        if self.state in [self.ASSESSING, self.DONE]:
            self.current_task=self.tasks[len(self.tasks)-1]
            return True

        self.current_task_xml=self.task_xml[self.current_task_number]
        current_task_type=self.get_tag_name(self.current_task_xml)
        if current_task_type=="selfassessment":
            self.current_task_descriptor=self_assessment_module.SelfAssessmentDescriptor(self.system)
            self.current_task_parsed_xml=self.current_task_descriptor.definition_from_xml(self.current_task_xml,self.system)
            self.current_task=self_assessment_module.SelfAssessmentModule(self.system, self.location, self.current_task_parsed_xml, self.current_task_descriptor)
        return True

    def get_html(self):
        return self.current_task.get_html()

    def handle_ajax(self, dispatch, get):
        return self.current_task.handle_ajax(dispatch,get)

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
        elt = etree.Element('selfassessment')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in ['task']:
            add_child(child)

        return elt