import json
import logging
from lxml import etree

from pkg_resources import resource_string

from xmodule.raw_module import RawDescriptor
from .x_module import XModule
from xblock.core import Integer, Scope, BlockScope, ModelType, String, Boolean, Object, Float
from xmodule.open_ended_grading_classes.combined_open_ended_modulev1 import CombinedOpenEndedV1Module, CombinedOpenEndedV1Descriptor

log = logging.getLogger("mitx.courseware")


V1_SETTINGS_ATTRIBUTES = ["display_name", "attempts", "is_graded", "accept_file_upload",
                 "skip_spelling_checks", "due", "graceperiod", "max_score"]

V1_STUDENT_ATTRIBUTES = ["current_task_number", "task_states", "state",
                          "student_attempts", "ready_to_reset"]

V1_ATTRIBUTES = V1_SETTINGS_ATTRIBUTES + V1_STUDENT_ATTRIBUTES

VERSION_TUPLES = (
    ('1', CombinedOpenEndedV1Descriptor, CombinedOpenEndedV1Module, V1_SETTINGS_ATTRIBUTES, V1_STUDENT_ATTRIBUTES),
)

DEFAULT_VERSION = 1
DEFAULT_VERSION = str(DEFAULT_VERSION)

class CombinedOpenEndedModule(XModule):
    """
    This is a module that encapsulates all open ended grading (self assessment, peer assessment, etc).
    It transitions between problems, and support arbitrary ordering.
    Each combined open ended module contains one or multiple "child" modules.
    Child modules track their own state, and can transition between states.  They also implement get_html and
    handle_ajax.
    The combined open ended module transitions between child modules as appropriate, tracks its own state, and passess
    ajax requests from the browser to the child module or handles them itself (in the cases of reset and next problem)
    ajax actions implemented by all children are:
        'save_answer' -- Saves the student answer
        'save_assessment' -- Saves the student assessment (or external grader assessment)
        'save_post_assessment' -- saves a post assessment (hint, feedback on feedback, etc)
    ajax actions implemented by combined open ended module are:
        'reset' -- resets the whole combined open ended module and returns to the first child module
        'next_problem' -- moves to the next child module
        'get_results' -- gets results from a given child module

    Types of children. Task is synonymous with child module, so each combined open ended module
    incorporates multiple children (tasks):
        openendedmodule
        selfassessmentmodule
    """
    STATE_VERSION = 1

    # states
    INITIAL = 'initial'
    ASSESSING = 'assessing'
    INTERMEDIATE_DONE = 'intermediate_done'
    DONE = 'done'

    icon_class = 'problem'

    display_name = String(help="Display name for this module", default="Open Ended Grading", scope=Scope.settings)
    current_task_number = Integer(help="Current task that the student is on.", default=0, scope=Scope.student_state)
    task_states = Object(help="State dictionaries of each task within this module.", default=[], scope=Scope.student_state)
    state = String(help="Which step within the current task that the student is on.", default="initial", scope=Scope.student_state)
    student_attempts = Integer(help="Number of attempts taken by the student on this problem", default=0, scope=Scope.student_state)
    ready_to_reset = Boolean(help="If the problem is ready to be reset or not.",  default=False, scope=Scope.student_state)
    attempts = Integer(help="Maximum number of attempts that a student is allowed.", default=1, scope=Scope.settings)
    is_graded = Boolean(help="Whether or not the problem is graded.",  default=False, scope=Scope.settings)
    accept_file_upload = Boolean(help="Whether or not the problem accepts file uploads.",  default=False, scope=Scope.settings)
    skip_spelling_checks = Boolean(help="Whether or not to skip initial spelling checks.",  default=True, scope=Scope.settings)
    due = String(help="Date that this problem is due by", default= None, scope=Scope.settings)
    graceperiod = String(help="Amount of time after the due date that submissions will be accepted", default=None, scope=Scope.settings)
    max_score = Integer(help="Maximum score for the problem.", default=1, scope=Scope.settings)
    version = Integer(help="Current version number", default=DEFAULT_VERSION, scope=Scope.settings)
    data = String(help="XML data for the problem", scope=Scope.content)

    js = {'coffee': [resource_string(__name__, 'js/src/combinedopenended/display.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/javascript_loader.coffee'),
    ]}
    js_module_name = "CombinedOpenEnded"

    css = {'scss': [resource_string(__name__, 'css/combinedopenended/display.scss')]}

    def __init__(self, system, location, descriptor, model_data):
        XModule.__init__(self, system, location, descriptor, model_data)

        """
        Definition file should have one or many task blocks, a rubric block, and a prompt block:

        Sample file:
        <combinedopenended attempts="10000" max_score="1">
            <rubric>
                Blah blah rubric.
            </rubric>
            <prompt>
                Some prompt.
            </prompt>
            <task>
                <selfassessment>
                    <hintprompt>
                        What hint about this problem would you give to someone?
                    </hintprompt>
                    <submitmessage>
                        Save Succcesful.  Thanks for participating!
                    </submitmessage>
                </selfassessment>
            </task>
            <task>
                <openended min_score_to_attempt="1" max_score_to_attempt="1">
                        <openendedparam>
                            <initial_display>Enter essay here.</initial_display>
                            <answer_display>This is the answer.</answer_display>
                            <grader_payload>{"grader_settings" : "ml_grading.conf",
                            "problem_id" : "6.002x/Welcome/OETest"}</grader_payload>
                        </openendedparam>
                </openended>
            </task>
        </combinedopenended>

        """

        self.system = system
        self.system.set('location', location)

        versions = [i[0] for i in VERSION_TUPLES]
        descriptors = [i[1] for i in VERSION_TUPLES]
        modules = [i[2] for i in VERSION_TUPLES]
        settings_attributes = [i[3] for i in VERSION_TUPLES]
        student_attributes = [i[4] for i in VERSION_TUPLES]

        try:
            version_index = versions.index(self.version)
        except:
            #This is a dev_facing_error
            log.error(version_error_string.format(self.version, DEFAULT_VERSION))
            self.version = DEFAULT_VERSION
            version_index = versions.index(self.version)

        self.student_attributes = student_attributes[version_index]
        self.settings_attributes = settings_attributes[version_index]

        attributes = self.student_attributes + self.settings_attributes

        static_data = {
            'rewrite_content_links' : self.rewrite_content_links,
        }
        instance_state = { k: getattr(self,k) for k in attributes}
        self.child_descriptor = descriptors[version_index](self.system)
        self.child_definition = descriptors[version_index].definition_from_xml(etree.fromstring(self.data), self.system)
        self.child_module = modules[version_index](self.system, location, self.child_definition, self.child_descriptor,
            instance_state = instance_state, static_data= static_data, model_data=model_data, attributes=attributes)

    def get_html(self):
        self.save_instance_data()
        return_value = self.child_module.get_html()
        return return_value

    def handle_ajax(self, dispatch, get):
        self.save_instance_data()
        return_value = self.child_module.handle_ajax(dispatch, get)
        self.save_instance_data()
        return return_value

    def get_instance_state(self):
        return self.child_module.get_instance_state()

    def get_score(self):
        return self.child_module.get_score()

    #def max_score(self):
    #    return self.child_module.max_score()

    def get_progress(self):
        return self.child_module.get_progress()

    @property
    def due_date(self):
        return self.child_module.due_date

    def save_instance_data(self):
        for attribute in self.student_attributes:
            setattr(self,attribute, getattr(self.child_module,attribute))


class CombinedOpenEndedDescriptor(RawDescriptor):
    """
    Module for adding combined open ended questions
    """
    mako_template = "widgets/raw-edit.html"
    module_class = CombinedOpenEndedModule
    filename_extension = "xml"

    stores_state = True
    has_score = True
    template_dir_name = "combinedopenended"

