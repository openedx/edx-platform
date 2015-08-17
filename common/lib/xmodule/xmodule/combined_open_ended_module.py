import logging

from lxml import etree
from pkg_resources import resource_string

from xmodule.raw_module import RawDescriptor
from .x_module import XModule, module_attr
from xblock.fields import Integer, Scope, String, List, Float, Boolean
from xmodule.open_ended_grading_classes.combined_open_ended_modulev1 import CombinedOpenEndedV1Module, CombinedOpenEndedV1Descriptor
from xmodule.validation import StudioValidation, StudioValidationMessage

from collections import namedtuple
from .fields import Date, Timedelta
import textwrap

log = logging.getLogger("edx.courseware")

# Make '_' a no-op so we can scrape strings
_ = lambda text: text

V1_SETTINGS_ATTRIBUTES = [
    "display_name",
    "max_attempts",
    "graded",
    "accept_file_upload",
    "skip_spelling_checks",
    "due",
    "graceperiod",
    "weight",
    "min_to_calibrate",
    "max_to_calibrate",
    "peer_grader_count",
    "required_peer_grading",
    "peer_grade_finished_submissions_when_none_pending",
]

V1_STUDENT_ATTRIBUTES = [
    "current_task_number",
    "task_states",
    "state",
    "student_attempts",
    "ready_to_reset",
    "old_task_states",
]

V1_ATTRIBUTES = V1_SETTINGS_ATTRIBUTES + V1_STUDENT_ATTRIBUTES

VersionTuple = namedtuple('VersionTuple', ['descriptor', 'module', 'settings_attributes', 'student_attributes'])
VERSION_TUPLES = {
    1: VersionTuple(CombinedOpenEndedV1Descriptor, CombinedOpenEndedV1Module, V1_SETTINGS_ATTRIBUTES,
                    V1_STUDENT_ATTRIBUTES),
}

DEFAULT_VERSION = 1
DEFAULT_DATA = textwrap.dedent("""\
<combinedopenended>
    <prompt>
        <h3>Censorship in the Libraries</h3>

        <p>'All of us can think of a book that we hope none of our children or any other children have taken off the shelf. But if I have the right to remove that book from the shelf -- that work I abhor -- then you also have exactly the same right and so does everyone else. And then we have no books left on the shelf for any of us.' --Katherine Paterson, Author
        </p>

        <p>
        Write a persuasive essay to a newspaper reflecting your views on censorship in libraries. Do you believe that certain materials, such as books, music, movies, magazines, etc., should be removed from the shelves if they are found offensive? Support your position with convincing arguments from your own experience, observations, and/or reading.
        </p>

    </prompt>
    <rubric>
        <rubric>
            <category>
                <description>
                Ideas
                </description>
                <option>
                Difficult for the reader to discern the main idea.  Too brief or too repetitive to establish or maintain a focus.
                </option>
                <option>
                Attempts a main idea.  Sometimes loses focus or ineffectively displays focus.
                </option>
                <option>
                Presents a unifying theme or main idea, but may include minor tangents.  Stays somewhat focused on topic and task.
                </option>
                <option>
                Presents a unifying theme or main idea without going off on tangents.  Stays completely focused on topic and task.
                </option>
            </category>
            <category>
                <description>
                Content
                </description>
                <option>
                Includes little information with few or no details or unrelated details.  Unsuccessful in attempts to explore any facets of the topic.
                </option>
                <option>
                Includes little information and few or no details.  Explores only one or two facets of the topic.
                </option>
                <option>
                Includes sufficient information and supporting details. (Details may not be fully developed; ideas may be listed.)  Explores some facets of the topic.
                </option>
                <option>
                Includes in-depth information and exceptional supporting details that are fully developed.  Explores all facets of the topic.
                </option>
            </category>
            <category>
            <description>
                Organization
                </description>
                <option>
                Ideas organized illogically, transitions weak, and response difficult to follow.
                </option>
                <option>
                Attempts to logically organize ideas.  Attempts to progress in an order that enhances meaning, and demonstrates use of transitions.
                </option>
                <option>
                Ideas organized logically.  Progresses in an order that enhances meaning.  Includes smooth transitions.
                </option>
            </category>
            <category>
                <description>
                Style
                </description>
                <option>
                Contains limited vocabulary, with many words used incorrectly.  Demonstrates problems with sentence patterns.
                </option>
                <option>
                Contains basic vocabulary, with words that are predictable and common.  Contains mostly simple sentences (although there may be an attempt at more varied sentence patterns).
                </option>
                <option>
                Includes vocabulary to make explanations detailed and precise.  Includes varied sentence patterns, including complex sentences.
                </option>
            </category>
            <category>
                <description>
                Voice
                </description>
                <option>
                Demonstrates language and tone that may be inappropriate to task and reader.
                </option>
                <option>
                Demonstrates an attempt to adjust language and tone to task and reader.
                </option>
                <option>
                Demonstrates effective adjustment of language and tone to task and reader.
                </option>

            </category>
        </rubric>
    </rubric>

    <task>
    <selfassessment/></task>
    <task>

        <openended min_score_to_attempt="4" max_score_to_attempt="12" >
            <openendedparam>
                <initial_display>Enter essay here.</initial_display>
                <answer_display>This is the answer.</answer_display>
                <grader_payload>{"grader_settings" : "ml_grading.conf", "problem_id" : "6.002x/Welcome/OETest"}</grader_payload>
            </openendedparam>
        </openended>
    </task>
    <task>

        <openended min_score_to_attempt="9" max_score_to_attempt="12" >
            <openendedparam>
                <initial_display>Enter essay here.</initial_display>
                <answer_display>This is the answer.</answer_display>
                <grader_payload>{"grader_settings" : "peer_grading.conf", "problem_id" : "6.002x/Welcome/OETest"}</grader_payload>
            </openendedparam>
        </openended>
    </task>

</combinedopenended>
""")


class VersionInteger(Integer):
    """
    A model type that converts from strings to integers when reading from json.
    Also does error checking to see if version is correct or not.
    """

    def from_json(self, value):
        try:
            value = int(value)
            if value not in VERSION_TUPLES:
                version_error_string = "Could not find version {0}, using version {1} instead"
                log.error(version_error_string.format(value, DEFAULT_VERSION))
                value = DEFAULT_VERSION
        except:
            value = DEFAULT_VERSION
        return value


class CombinedOpenEndedFields(object):
    display_name = String(
        display_name=_("Display Name"),
        help=_("This name appears in the horizontal navigation at the top of the page."),
        default=_("Open Response Assessment"),
        scope=Scope.settings
    )
    current_task_number = Integer(
        help=_("Current task that the student is on."),
        default=0,
        scope=Scope.user_state
    )
    old_task_states = List(
        help=_("A list of lists of state dictionaries for student states that are saved. "
               "This field is only populated if the instructor changes tasks after "
               "the module is created and students have attempted it (for example, if a self assessed problem is "
               "changed to self and peer assessed)."),
        scope=Scope.user_state,
    )
    task_states = List(
        help=_("List of state dictionaries of each task within this module."),
        scope=Scope.user_state
    )
    state = String(
        help=_("Which step within the current task that the student is on."),
        default="initial",
        scope=Scope.user_state
    )
    graded = Boolean(
        display_name=_("Graded"),
        help=_("Defines whether the student gets credit for this problem. Credit is based on peer grades of this problem."),
        default=False,
        scope=Scope.settings
    )
    student_attempts = Integer(
        help=_("Number of attempts taken by the student on this problem"),
        default=0,
        scope=Scope.user_state
    )
    ready_to_reset = Boolean(
        help=_("If the problem is ready to be reset or not."),
        default=False,
        scope=Scope.user_state
    )
    max_attempts = Integer(
        display_name=_("Maximum Attempts"),
        help=_("The number of times the student can try to answer this problem."),
        default=1,
        scope=Scope.settings,
        values={"min": 1}
    )
    accept_file_upload = Boolean(
        display_name=_("Allow File Uploads"),
        help=_("Whether or not the student can submit files as a response."),
        default=False,
        scope=Scope.settings
    )
    skip_spelling_checks = Boolean(
        display_name=_("Disable Quality Filter"),
        help=_("If False, the Quality Filter is enabled and submissions with poor spelling, short length, or poor grammar will not be peer reviewed."),
        default=False,
        scope=Scope.settings
    )
    due = Date(
        help=_("Date that this problem is due by"),
        scope=Scope.settings
    )
    graceperiod = Timedelta(
        help=_("Amount of time after the due date that submissions will be accepted"),
        scope=Scope.settings
    )
    version = VersionInteger(
        help=_("Current version number"),
        default=DEFAULT_VERSION,
        scope=Scope.settings)
    data = String(
        help=_("XML data for the problem"),
        scope=Scope.content,
        default=DEFAULT_DATA)
    weight = Float(
        display_name=_("Problem Weight"),
        help=_("Defines the number of points each problem is worth. If the value is not set, each problem is worth one point."),
        scope=Scope.settings,
        values={"min": 0, "step": ".1"},
        default=1
    )
    min_to_calibrate = Integer(
        display_name=_("Minimum Peer Grading Calibrations"),
        help=_("The minimum number of calibration essays each student will need to complete for peer grading."),
        default=3,
        scope=Scope.settings,
        values={"min": 1, "max": 20, "step": "1"}
    )
    max_to_calibrate = Integer(
        display_name=_("Maximum Peer Grading Calibrations"),
        help=_("The maximum number of calibration essays each student will need to complete for peer grading."),
        default=6,
        scope=Scope.settings,
        values={"min": 1, "max": 20, "step": "1"}
    )
    peer_grader_count = Integer(
        display_name=_("Peer Graders per Response"),
        help=_("The number of peers who will grade each submission."),
        default=3,
        scope=Scope.settings,
        values={"min": 1, "step": "1", "max": 5}
    )
    required_peer_grading = Integer(
        display_name=_("Required Peer Grading"),
        help=_("The number of other students each student making a submission will have to grade."),
        default=3,
        scope=Scope.settings,
        values={"min": 1, "step": "1", "max": 5}
    )
    peer_grade_finished_submissions_when_none_pending = Boolean(
        display_name=_('Allow "overgrading" of peer submissions'),
        help=_(
            "EXPERIMENTAL FEATURE.  Allow students to peer grade submissions that already have the requisite number of graders, "
            "but ONLY WHEN all submissions they are eligible to grade already have enough graders.  "
            "This is intended for use when settings for `Required Peer Grading` > `Peer Graders per Response`"
        ),
        default=False,
        scope=Scope.settings,
    )
    markdown = String(
        help=_("Markdown source of this module"),
        default=textwrap.dedent("""\
                    [prompt]
                        <h3>Censorship in the Libraries</h3>

                        <p>'All of us can think of a book that we hope none of our children or any other children have taken off the shelf. But if I have the right to remove that book from the shelf -- that work I abhor -- then you also have exactly the same right and so does everyone else. And then we have no books left on the shelf for any of us.' --Katherine Paterson, Author
                        </p>

                        <p>
                        Write a persuasive essay to a newspaper reflecting your views on censorship in libraries. Do you believe that certain materials, such as books, music, movies, magazines, etc., should be removed from the shelves if they are found offensive? Support your position with convincing arguments from your own experience, observations, and/or reading.
                        </p>
                    [prompt]
                    [rubric]
                    + Ideas
                    - Difficult for the reader to discern the main idea.  Too brief or too repetitive to establish or maintain a focus.
                    - Attempts a main idea.  Sometimes loses focus or ineffectively displays focus.
                    - Presents a unifying theme or main idea, but may include minor tangents.  Stays somewhat focused on topic and task.
                    - Presents a unifying theme or main idea without going off on tangents.  Stays completely focused on topic and task.
                    + Content
                    - Includes little information with few or no details or unrelated details.  Unsuccessful in attempts to explore any facets of the topic.
                    - Includes little information and few or no details.  Explores only one or two facets of the topic.
                    - Includes sufficient information and supporting details. (Details may not be fully developed; ideas may be listed.)  Explores some facets of the topic.
                    - Includes in-depth information and exceptional supporting details that are fully developed.  Explores all facets of the topic.
                    + Organization
                    - Ideas organized illogically, transitions weak, and response difficult to follow.
                    - Attempts to logically organize ideas.  Attempts to progress in an order that enhances meaning, and demonstrates use of transitions.
                    - Ideas organized logically.  Progresses in an order that enhances meaning.  Includes smooth transitions.
                    + Style
                    - Contains limited vocabulary, with many words used incorrectly.  Demonstrates problems with sentence patterns.
                    - Contains basic vocabulary, with words that are predictable and common.  Contains mostly simple sentences (although there may be an attempt at more varied sentence patterns).
                    - Includes vocabulary to make explanations detailed and precise.  Includes varied sentence patterns, including complex sentences.
                    + Voice
                    - Demonstrates language and tone that may be inappropriate to task and reader.
                    - Demonstrates an attempt to adjust language and tone to task and reader.
                    - Demonstrates effective adjustment of language and tone to task and reader.
                    [rubric]
                    [tasks]
                    (Self), ({4-12}AI), ({9-12}Peer)
                    [tasks]

        """),
        scope=Scope.settings
    )


class CombinedOpenEndedModule(CombinedOpenEndedFields, XModule):
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

    CombinedOpenEndedModule.__init__ takes the same arguments as xmodule.x_module:XModule.__init__
    """
    STATE_VERSION = 1

    # states
    INITIAL = 'initial'
    ASSESSING = 'assessing'
    INTERMEDIATE_DONE = 'intermediate_done'
    DONE = 'done'

    icon_class = 'problem'

    js = {
        'coffee': [
            resource_string(__name__, 'js/src/combinedopenended/display.coffee'),
            resource_string(__name__, 'js/src/javascript_loader.coffee'),
        ],
        'js': [
            resource_string(__name__, 'js/src/collapsible.js'),
        ]
    }
    js_module_name = "CombinedOpenEnded"

    css = {'scss': [resource_string(__name__, 'css/combinedopenended/display.scss')]}

    def __init__(self, *args, **kwargs):
        """
        Definition file should have one or many task blocks, a rubric block, and a prompt block.

        See DEFAULT_DATA for a sample.

        """
        super(CombinedOpenEndedModule, self).__init__(*args, **kwargs)

        self.system.set('location', self.location)

        if self.task_states is None:
            self.task_states = []

        if self.old_task_states is None:
            self.old_task_states = []

        version_tuple = VERSION_TUPLES[self.version]

        self.student_attributes = version_tuple.student_attributes
        self.settings_attributes = version_tuple.settings_attributes

        attributes = self.student_attributes + self.settings_attributes

        static_data = {}
        instance_state = {k: getattr(self, k) for k in attributes}
        self.child_descriptor = version_tuple.descriptor(self.system)
        self.child_definition = version_tuple.descriptor.definition_from_xml(etree.fromstring(self.data), self.system)
        self.child_module = version_tuple.module(self.system, self.location, self.child_definition, self.child_descriptor,
                                                 instance_state=instance_state, static_data=static_data,
                                                 attributes=attributes)
        self.save_instance_data()

    def get_html(self):
        self.save_instance_data()
        return_value = self.child_module.get_html()
        return return_value

    def handle_ajax(self, dispatch, data):
        self.save_instance_data()
        return_value = self.child_module.handle_ajax(dispatch, data)
        self.save_instance_data()
        return return_value

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

    def save_instance_data(self):
        for attribute in self.student_attributes:
            setattr(self, attribute, getattr(self.child_module, attribute))

    def validate(self):
        """
        Message for either error or warning validation message/s.

        Returns message and type. Priority given to error type message.
        """
        return self.descriptor.validate()


class CombinedOpenEndedDescriptor(CombinedOpenEndedFields, RawDescriptor):
    """
    Module for adding combined open ended questions
    """
    mako_template = "widgets/open-ended-edit.html"
    module_class = CombinedOpenEndedModule

    has_score = True
    always_recalculate_grades = True
    template_dir_name = "combinedopenended"

    #Specify whether or not to pass in S3 interface
    needs_s3_interface = True

    #Specify whether or not to pass in open ended interface
    needs_open_ended_interface = True

    js = {'coffee': [resource_string(__name__, 'js/src/combinedopenended/edit.coffee')]}
    js_module_name = "OpenEndedMarkdownEditingDescriptor"
    css = {'scss': [resource_string(__name__, 'css/editor/edit.scss'), resource_string(__name__, 'css/combinedopenended/edit.scss')]}

    metadata_translations = {
        'is_graded': 'graded',
        'attempts': 'max_attempts',
    }

    def get_context(self):
        _context = RawDescriptor.get_context(self)
        _context.update({'markdown': self.markdown,
                         'enable_markdown': self.markdown is not None})
        return _context

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(CombinedOpenEndedDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([CombinedOpenEndedDescriptor.due, CombinedOpenEndedDescriptor.graceperiod,
                                    CombinedOpenEndedDescriptor.markdown, CombinedOpenEndedDescriptor.version])
        return non_editable_fields

    # Proxy to CombinedOpenEndedModule so that external callers don't have to know if they're working
    # with a module or a descriptor
    child_module = module_attr('child_module')

    def validate(self):
        """
        Validates the state of this instance. This is the override of the general XBlock method,
        and it will also ask its superclass to validate.
        """
        validation = super(CombinedOpenEndedDescriptor, self).validate()
        validation = StudioValidation.copy(validation)

        i18n_service = self.runtime.service(self, "i18n")

        validation.summary = StudioValidationMessage(
            StudioValidationMessage.ERROR,
            i18n_service.ugettext(
                "ORA1 is no longer supported. To use this assessment, "
                "replace this ORA1 component with an ORA2 component."
            )
        )
        return validation
