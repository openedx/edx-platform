import json
import logging
from lxml import etree

from pkg_resources import resource_string

from xmodule.raw_module import RawDescriptor
from .x_module import XModule
from xmodule.open_ended_grading_classes.combined_open_ended_modulev1 import CombinedOpenEndedV1Module, CombinedOpenEndedV1Descriptor

log = logging.getLogger("mitx.courseware")


VERSION_TUPLES = (
    ('1', CombinedOpenEndedV1Descriptor, CombinedOpenEndedV1Module),
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

    js = {'coffee': [resource_string(__name__, 'js/src/combinedopenended/display.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/javascript_loader.coffee'),
    ]}
    js_module_name = "CombinedOpenEnded"

    css = {'scss': [resource_string(__name__, 'css/combinedopenended/display.scss')]}

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
            instance_state, shared_state, **kwargs)

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

        # Load instance state
        if instance_state is not None:
            instance_state = json.loads(instance_state)
        else:
            instance_state = {}

        self.version = self.metadata.get('version', DEFAULT_VERSION)
        version_error_string = "Version of combined open ended module {0} is not correct.  Going with version {1}"
        if not isinstance(self.version, basestring):
            try:
                self.version = str(self.version)
            except:
                #This is a dev_facing_error
                log.info(version_error_string.format(self.version, DEFAULT_VERSION))
                self.version = DEFAULT_VERSION

        versions = [i[0] for i in VERSION_TUPLES]
        descriptors = [i[1] for i in VERSION_TUPLES]
        modules = [i[2] for i in VERSION_TUPLES]

        try:
            version_index = versions.index(self.version)
        except:
            #This is a dev_facing_error
            log.error(version_error_string.format(self.version, DEFAULT_VERSION))
            self.version = DEFAULT_VERSION
            version_index = versions.index(self.version)

        static_data = {
            'rewrite_content_links' : self.rewrite_content_links,
        }

        self.child_descriptor = descriptors[version_index](self.system)
        self.child_definition = descriptors[version_index].definition_from_xml(etree.fromstring(definition['data']), self.system)
        self.child_module = modules[version_index](self.system, location, self.child_definition, self.child_descriptor,
            instance_state = json.dumps(instance_state), metadata = self.metadata, static_data= static_data)

    def get_html(self):
        return self.child_module.get_html()

    def handle_ajax(self, dispatch, get):
        return self.child_module.handle_ajax(dispatch, get)

    def get_instance_state(self):
        return self.child_module.get_instance_state()

    def get_score(self):
        return self.child_module.get_score()

    def max_score(self):
        return self.child_module.max_score()

    def get_progress(self):
        return self.child_module.get_progress()

    @property
    def due_date(self):
        return self.child_module.due_date

    @property
    def display_name(self):
        return self.child_module.display_name


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

