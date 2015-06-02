import json
import logging
import traceback
from lxml import etree
from xmodule.timeinfo import TimeInfo
from xmodule.capa_module import ComplexEncoder
from xmodule.progress import Progress
from xmodule.stringify import stringify_children
from xmodule.open_ended_grading_classes import self_assessment_module
from xmodule.open_ended_grading_classes import open_ended_module
from .combined_open_ended_rubric import CombinedOpenEndedRubric, GRADER_TYPE_IMAGE_DICT, HUMAN_GRADER_TYPE, LEGEND_LIST
from xmodule.open_ended_grading_classes.peer_grading_service import PeerGradingService, MockPeerGradingService
from xmodule.open_ended_grading_classes.openendedchild import OpenEndedChild
from xmodule.open_ended_grading_classes.grading_service_module import GradingServiceError

log = logging.getLogger("edx.courseware")

# Set the default number of max attempts.  Should be 1 for production
# Set higher for debugging/testing
# attempts specified in xml definition overrides this.
MAX_ATTEMPTS = 1

# The highest score allowed for the overall xmodule and for each rubric point
MAX_SCORE_ALLOWED = 50

# If true, default behavior is to score module as a practice problem.  Otherwise, no grade at all is shown in progress
# Metadata overrides this.
IS_SCORED = False

# If true, then default behavior is to require a file upload or pasted link from a student for this problem.
# Metadata overrides this.
ACCEPT_FILE_UPLOAD = False

# Contains all reasonable bool and case combinations of True
TRUE_DICT = ["True", True, "TRUE", "true"]

_ = lambda text: text

HUMAN_TASK_TYPE = {
    # Translators: "Self" is used to denote an openended response that is self-graded
    'selfassessment': _("Self"),
    'openended': "edX",
    # Translators: "AI" is used to denote an openended response that is machine-graded
    'ml_grading.conf': _("AI"),
    # Translators: "Peer" is used to denote an openended response that is peer-graded
    'peer_grading.conf': _("Peer"),
}

HUMAN_STATES = {
    # Translators: "Not started" is used to communicate to a student that their response
    # has not yet been graded
    'intitial': _("Not started."),
    # Translators: "Being scored." is used to communicate to a student that their response
    # are in the process of being scored
    'assessing': _("Being scored."),
    # Translators: "Scoring finished" is used to communicate to a student that their response
    # have been scored, but the full scoring process is not yet complete
    'intermediate_done': _("Scoring finished."),
    # Translators: "Complete" is used to communicate to a student that their
    # openended response has been fully scored
    'done': _("Complete."),
}

# Default value that controls whether or not to skip basic spelling checks in the controller
# Metadata overrides this
SKIP_BASIC_CHECKS = False


class CombinedOpenEndedV1Module(object):
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
        'reset' -- resets the whole combined open ended module and returns to the first child moduleresource_string
        'next_problem' -- moves to the next child module

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

    # Where the templates live for this problem
    TEMPLATE_DIR = "combinedopenended"

    # hack: included to make this class act enough like an xblock to get i18n
    _services_requested = {"i18n": "need"}
    _combined_services = _services_requested

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, metadata=None, static_data=None, **kwargs):

        """
        Definition file should have one or many task blocks, a rubric block, and a prompt block.  See DEFAULT_DATA in combined_open_ended_module for a sample.

        """
        self.instance_state = instance_state
        self.display_name = instance_state.get('display_name', "Open Ended")

        # We need to set the location here so the child modules can use it
        system.set('location', location)
        self.system = system

        # Tells the system which xml definition to load
        self.current_task_number = instance_state.get('current_task_number', 0)
        # This loads the states of the individual children
        self.task_states = instance_state.get('task_states', [])
        #This gets any old task states that have been persisted after the instructor changed the tasks.
        self.old_task_states = instance_state.get('old_task_states', [])
        # Overall state of the combined open ended module
        self.state = instance_state.get('state', self.INITIAL)

        self.student_attempts = instance_state.get('student_attempts', 0)
        self.weight = instance_state.get('weight', 1)

        # Allow reset is true if student has failed the criteria to move to the next child task
        self.ready_to_reset = instance_state.get('ready_to_reset', False)
        self.max_attempts = instance_state.get('max_attempts', MAX_ATTEMPTS)
        self.is_scored = instance_state.get('graded', IS_SCORED) in TRUE_DICT
        self.accept_file_upload = instance_state.get('accept_file_upload', ACCEPT_FILE_UPLOAD) in TRUE_DICT
        self.skip_basic_checks = instance_state.get('skip_spelling_checks', SKIP_BASIC_CHECKS) in TRUE_DICT

        if system.open_ended_grading_interface:
            self.peer_gs = PeerGradingService(system.open_ended_grading_interface, system.render_template)
        else:
            self.peer_gs = MockPeerGradingService()

        self.required_peer_grading = instance_state.get('required_peer_grading', 3)
        self.peer_grader_count = instance_state.get('peer_grader_count', 3)
        self.min_to_calibrate = instance_state.get('min_to_calibrate', 3)
        self.max_to_calibrate = instance_state.get('max_to_calibrate', 6)
        self.peer_grade_finished_submissions_when_none_pending = instance_state.get(
            'peer_grade_finished_submissions_when_none_pending', False
        )

        due_date = instance_state.get('due', None)
        grace_period_string = instance_state.get('graceperiod', None)
        try:
            self.timeinfo = TimeInfo(due_date, grace_period_string)
        except Exception:
            log.error("Error parsing due date information in location {0}".format(location))
            raise
        self.display_due_date = self.timeinfo.display_due_date

        self.rubric_renderer = CombinedOpenEndedRubric(system.render_template, True)
        rubric_string = stringify_children(definition['rubric'])
        self._max_score = self.rubric_renderer.check_if_rubric_is_parseable(rubric_string, location, MAX_SCORE_ALLOWED)

        # Static data is passed to the child modules to render
        self.static_data = {
            'max_score': self._max_score,
            'max_attempts': self.max_attempts,
            'prompt': definition['prompt'],
            'rubric': definition['rubric'],
            'display_name': self.display_name,
            'accept_file_upload': self.accept_file_upload,
            'close_date': self.timeinfo.close_date,
            's3_interface': self.system.s3_interface,
            'skip_basic_checks': self.skip_basic_checks,
            'control': {
                'required_peer_grading': self.required_peer_grading,
                'peer_grader_count': self.peer_grader_count,
                'min_to_calibrate': self.min_to_calibrate,
                'max_to_calibrate': self.max_to_calibrate,
                'peer_grade_finished_submissions_when_none_pending': (
                    self.peer_grade_finished_submissions_when_none_pending
                ),
            }
        }

        self.task_xml = definition['task_xml']
        self.location = location
        self.fix_invalid_state()
        self.setup_next_task()

    def validate_task_states(self, tasks_xml, task_states):
        """
        Check whether the provided task_states are valid for the supplied task_xml.

        Returns a list of messages indicating what is invalid about the state.
        If the list is empty, then the state is valid
        """
        msgs = []
        #Loop through each task state and make sure it matches the xml definition
        for task_xml, task_state in zip(tasks_xml, task_states):
            tag_name = self.get_tag_name(task_xml)
            children = self.child_modules()
            task_descriptor = children['descriptors'][tag_name](self.system)
            task_parsed_xml = task_descriptor.definition_from_xml(etree.fromstring(task_xml), self.system)
            try:
                task = children['modules'][tag_name](
                    self.system,
                    self.location,
                    task_parsed_xml,
                    task_descriptor,
                    self.static_data,
                    instance_state=task_state,
                )
                #Loop through each attempt of the task and see if it is valid.
                for attempt in task.child_history:
                    if "post_assessment" not in attempt:
                        continue
                    post_assessment = attempt['post_assessment']
                    try:
                        post_assessment = json.loads(post_assessment)
                    except ValueError:
                        #This is okay, the value may or may not be json encoded.
                        pass
                    if tag_name == "openended" and isinstance(post_assessment, list):
                        msgs.append("Type is open ended and post assessment is a list.")
                        break
                    elif tag_name == "selfassessment" and not isinstance(post_assessment, list):
                        msgs.append("Type is self assessment and post assessment is not a list.")
                        break
                #See if we can properly render the task.  Will go into the exception clause below if not.
                task.get_html(self.system)
            except Exception:
                #If one task doesn't match, the state is invalid.
                msgs.append("Could not parse task with xml {xml!r} and states {state!r}: {err}".format(
                    xml=task_xml,
                    state=task_state,
                    err=traceback.format_exc()
                ))
                break
        return msgs

    def is_initial_child_state(self, task_child):
        """
        Returns true if this is a child task in an initial configuration
        """
        task_child = json.loads(task_child)
        return (
            task_child['child_state'] == self.INITIAL and
            task_child['child_history'] == []
        )

    def is_reset_task_states(self, task_state):
        """
        Returns True if this task_state is from something that was just reset
        """
        return all(self.is_initial_child_state(child) for child in task_state)

    def states_sort_key(self, idx_task_states):
        """
        Return a key for sorting a list of indexed task_states, by how far the student got
        through the tasks, what their highest score was, and then the index of the submission.
        """
        idx, task_states = idx_task_states

        state_values = {
            OpenEndedChild.INITIAL: 0,
            OpenEndedChild.ASSESSING: 1,
            OpenEndedChild.POST_ASSESSMENT: 2,
            OpenEndedChild.DONE: 3
        }

        if not task_states:
            return (0, 0, state_values[OpenEndedChild.INITIAL], idx)

        final_task_xml = self.task_xml[-1]
        final_child_state_json = task_states[-1]
        final_child_state = json.loads(final_child_state_json)

        tag_name = self.get_tag_name(final_task_xml)
        children = self.child_modules()
        task_descriptor = children['descriptors'][tag_name](self.system)
        task_parsed_xml = task_descriptor.definition_from_xml(etree.fromstring(final_task_xml), self.system)
        task = children['modules'][tag_name](
            self.system,
            self.location,
            task_parsed_xml,
            task_descriptor,
            self.static_data,
            instance_state=final_child_state_json,
        )
        scores = task.all_scores()
        if scores:
            best_score = max(scores)
        else:
            best_score = 0
        return (
            len(task_states),
            best_score,
            state_values.get(final_child_state.get('child_state', OpenEndedChild.INITIAL), 0),
            idx
        )

    def fix_invalid_state(self):
        """
        Sometimes a teacher will change the xml definition of a problem in Studio.
        This means that the state passed to the module is invalid.
        If that is the case, moved it to old_task_states and delete task_states.
        """

        # If we are on a task that is greater than the number of available tasks,
        # it is an invalid state. If the current task number is greater than the number of tasks
        # we have in the definition, our state is invalid.
        if self.current_task_number > len(self.task_states) or self.current_task_number > len(self.task_xml):
            self.current_task_number = max(min(len(self.task_states), len(self.task_xml)) - 1, 0)
        #If the length of the task xml is less than the length of the task states, state is invalid
        if len(self.task_xml) < len(self.task_states):
            self.current_task_number = len(self.task_xml) - 1
            self.task_states = self.task_states[:len(self.task_xml)]

        if not self.old_task_states and not self.task_states:
            # No validation needed when a student first looks at the problem
            return

        # Pick out of self.task_states and self.old_task_states the state that is
        # a) valid for the current task definition
        # b) not the result of a reset due to not having a valid task state
        # c) has the highest total score
        # d) is the most recent (if the other two conditions are met)

        valid_states = [
            task_states
            for task_states
            in self.old_task_states + [self.task_states]
            if (
                len(self.validate_task_states(self.task_xml, task_states)) == 0 and
                not self.is_reset_task_states(task_states)
            )
        ]

        # If there are no valid states, don't try and use an old state
        if len(valid_states) == 0:
            # If this isn't an initial task state, then reset to an initial state
            if not self.is_reset_task_states(self.task_states):
                self.reset_task_state('\n'.join(self.validate_task_states(self.task_xml, self.task_states)))

            return

        sorted_states = sorted(enumerate(valid_states), key=self.states_sort_key, reverse=True)
        idx, best_task_states = sorted_states[0]

        if best_task_states == self.task_states:
            return

        log.warning(
            "Updating current task state for %s to %r for student with anonymous id %r",
            self.system.location,
            best_task_states,
            self.system.anonymous_student_id
        )

        self.old_task_states.remove(best_task_states)
        self.old_task_states.append(self.task_states)
        self.task_states = best_task_states

        # The state is ASSESSING unless all of the children are done, or all
        # of the children haven't been started yet
        children = [json.loads(child) for child in best_task_states]
        if all(child['child_state'] == self.DONE for child in children):
            self.state = self.DONE
        elif all(child['child_state'] == self.INITIAL for child in children):
            self.state = self.INITIAL
        else:
            self.state = self.ASSESSING

        # The current task number is the index of the last completed child + 1,
        # limited by the number of tasks
        last_completed_child = next((i for i, child in reversed(list(enumerate(children))) if child['child_state'] == self.DONE), 0)
        self.current_task_number = min(last_completed_child + 1, len(best_task_states) - 1)

    def create_task(self, task_state, task_xml):
        """Create task object for given task state and task xml."""

        tag_name = self.get_tag_name(task_xml)
        children = self.child_modules()
        task_descriptor = children['descriptors'][tag_name](self.system)
        task_parsed_xml = task_descriptor.definition_from_xml(etree.fromstring(task_xml), self.system)
        task = children['modules'][tag_name](
            self.system,
            self.location,
            task_parsed_xml,
            task_descriptor,
            self.static_data,
            instance_state=task_state,
        )
        return task

    def get_task_number(self, task_number):
        """Return task object at task_index."""

        task_states_count = len(self.task_states)
        if task_states_count > 0 and task_number < task_states_count:
            task_state = self.task_states[task_number]
            task_xml = self.task_xml[task_number]
            return self.create_task(task_state, task_xml)
        return None

    def reset_task_state(self, message=""):
        """
        Resets the task states.  Moves current task state to an old_state variable, and then makes the task number 0.
        :param message: A message to put in the log.
        :return: None
        """
        info_message = "Combined open ended user state for user {0} in location {1} was invalid.  It has been reset, and you now have a new attempt. {2}".format(self.system.anonymous_student_id, self.location.to_deprecated_string(), message)
        self.current_task_number = 0
        self.student_attempts = 0
        self.old_task_states.append(self.task_states)
        self.task_states = []
        log.info(info_message)

    def get_tag_name(self, xml):
        """
        Gets the tag name of a given xml block.
        Input: XML string
        Output: The name of the root tag
        """
        tag = etree.fromstring(xml).tag
        return tag

    def overwrite_state(self, current_task_state):
        """
        Overwrites an instance state and sets the latest response to the current response.  This is used
        to ensure that the student response is carried over from the first child to the rest.
        Input: Task state json string
        Output: Task state json string
        """
        last_response_data = self.get_last_response(self.current_task_number - 1)
        last_response = last_response_data['response']

        loaded_task_state = json.loads(current_task_state)
        if loaded_task_state['child_state'] == self.INITIAL:
            loaded_task_state['child_state'] = self.ASSESSING
            loaded_task_state['child_created'] = True
            loaded_task_state['child_history'].append({'answer': last_response})
            current_task_state = json.dumps(loaded_task_state)
        return current_task_state

    def child_modules(self):
        """
        Returns the constructors associated with the child modules in a dictionary.  This makes writing functions
        simpler (saves code duplication)
        Input: None
        Output: A dictionary of dictionaries containing the descriptor functions and module functions
        """
        child_modules = {
            'openended': open_ended_module.OpenEndedModule,
            'selfassessment': self_assessment_module.SelfAssessmentModule,
        }
        child_descriptors = {
            'openended': open_ended_module.OpenEndedDescriptor,
            'selfassessment': self_assessment_module.SelfAssessmentDescriptor,
        }
        children = {
            'modules': child_modules,
            'descriptors': child_descriptors,
        }
        return children

    def setup_next_task(self, reset=False):
        """
        Sets up the next task for the module.  Creates an instance state if none exists, carries over the answer
        from the last instance state to the next if needed.
        Input: A boolean indicating whether or not the reset function is calling.
        Output: Boolean True (not useful right now)
        """
        current_task_state = None
        if len(self.task_states) > self.current_task_number:
            current_task_state = self.task_states[self.current_task_number]

        self.current_task_xml = self.task_xml[self.current_task_number]

        if self.current_task_number > 0:
            self.ready_to_reset = self.check_allow_reset()
            if self.ready_to_reset:
                self.current_task_number = self.current_task_number - 1

        current_task_type = self.get_tag_name(self.current_task_xml)

        children = self.child_modules()
        child_task_module = children['modules'][current_task_type]

        self.current_task_descriptor = children['descriptors'][current_task_type](self.system)

        # This is the xml object created from the xml definition of the current task
        etree_xml = etree.fromstring(self.current_task_xml)

        # This sends the etree_xml object through the descriptor module of the current task, and
        # returns the xml parsed by the descriptor
        self.current_task_parsed_xml = self.current_task_descriptor.definition_from_xml(etree_xml, self.system)
        if current_task_state is None and self.current_task_number == 0:
            self.current_task = child_task_module(self.system, self.location,
                                                  self.current_task_parsed_xml, self.current_task_descriptor,
                                                  self.static_data)
            self.task_states.append(self.current_task.get_instance_state())
            self.state = self.ASSESSING
        elif current_task_state is None and self.current_task_number > 0:
            last_response_data = self.get_last_response(self.current_task_number - 1)
            last_response = last_response_data['response']
            current_task_state = json.dumps({
                'child_state': self.ASSESSING,
                'version': self.STATE_VERSION,
                'max_score': self._max_score,
                'child_attempts': 0,
                'child_created': True,
                'child_history': [{'answer': last_response}],
            })
            self.current_task = child_task_module(self.system, self.location,
                                                  self.current_task_parsed_xml, self.current_task_descriptor,
                                                  self.static_data,
                                                  instance_state=current_task_state)
            self.task_states.append(self.current_task.get_instance_state())
            self.state = self.ASSESSING
        else:
            if self.current_task_number > 0 and not reset:
                current_task_state = self.overwrite_state(current_task_state)
            self.current_task = child_task_module(self.system, self.location,
                                                  self.current_task_parsed_xml, self.current_task_descriptor,
                                                  self.static_data,
                                                  instance_state=current_task_state)

        return True

    def check_allow_reset(self):
        """
        Checks to see if the student has passed the criteria to move to the next module.  If not, sets
        allow_reset to true and halts the student progress through the tasks.
        Input: None
        Output: the allow_reset attribute of the current module.
        """
        if not self.ready_to_reset:
            if self.current_task_number > 0:
                last_response_data = self.get_last_response(self.current_task_number - 1)
                current_response_data = self.get_current_attributes(self.current_task_number)

                if current_response_data['min_score_to_attempt'] > last_response_data['score'] or\
                   current_response_data['max_score_to_attempt'] < last_response_data['score']:
                    self.state = self.DONE
                    self.ready_to_reset = True

        return self.ready_to_reset

    def get_context(self):
        """
        Generates a context dictionary that is used to render html.
        Input: None
        Output: A dictionary that can be rendered into the combined open ended template.
        """
        task_html = self.get_html_base()
        # set context variables and render template
        ugettext = self.system.service(self, "i18n").ugettext

        context = {
            'items': [{'content': task_html}],
            'ajax_url': self.system.ajax_url,
            'allow_reset': self.ready_to_reset,
            'state': self.state,
            'task_count': len(self.task_xml),
            'task_number': self.current_task_number + 1,
            'status': ugettext(self.get_status(False)),    # pylint: disable=translation-of-non-string
            'display_name': self.display_name,
            'accept_file_upload': self.accept_file_upload,
            'location': self.location,
            'legend_list': LEGEND_LIST,
            'human_state': ugettext(HUMAN_STATES.get(self.state, HUMAN_STATES["intitial"])),    # pylint: disable=translation-of-non-string
            'is_staff': self.system.user_is_staff,
        }

        return context

    def get_html(self):
        """
        Gets HTML for rendering.
        Input: None
        Output: rendered html
        """
        context = self.get_context()
        html = self.system.render_template(
            '{0}/combined_open_ended.html'.format(self.TEMPLATE_DIR), context
        )
        return html

    def get_html_nonsystem(self):
        """
        Gets HTML for rendering via AJAX.  Does not use system, because system contains some additional
        html, which is not appropriate for returning via ajax calls.
        Input: None
        Output: HTML rendered directly via Mako
        """
        context = self.get_context()
        html = self.system.render_template(
            '{0}/combined_open_ended.html'.format(self.TEMPLATE_DIR), context
        )
        return html

    def get_html_base(self):
        """
        Gets the HTML associated with the current child task
        Input: None
        Output: Child task HTML
        """
        self.update_task_states()
        return self.current_task.get_html(self.system)

    def get_html_ajax(self, data):
        """
        Get HTML in AJAX callback
        data - Needed to preserve AJAX structure
        Output: Dictionary with html attribute
        """
        return {'html': self.get_html()}

    def get_current_attributes(self, task_number):
        """
        Gets the min and max score to attempt attributes of the specified task.
        Input: The number of the task.
        Output: The minimum and maximum scores needed to move on to the specified task.
        """
        task_xml = self.task_xml[task_number]
        etree_xml = etree.fromstring(task_xml)
        min_score_to_attempt = int(etree_xml.attrib.get('min_score_to_attempt', 0))
        max_score_to_attempt = int(etree_xml.attrib.get('max_score_to_attempt', self._max_score))
        return {'min_score_to_attempt': min_score_to_attempt, 'max_score_to_attempt': max_score_to_attempt}

    def get_last_response(self, task_number):
        """
        Returns data associated with the specified task number, such as the last response, score, etc.
        Input: The number of the task.
        Output: A dictionary that contains information about the specified task.
        """
        last_response = ""
        task_state = self.task_states[task_number]
        task_xml = self.task_xml[task_number]
        task_type = self.get_tag_name(task_xml)

        children = self.child_modules()

        task_descriptor = children['descriptors'][task_type](self.system)
        etree_xml = etree.fromstring(task_xml)

        min_score_to_attempt = int(etree_xml.attrib.get('min_score_to_attempt', 0))
        max_score_to_attempt = int(etree_xml.attrib.get('max_score_to_attempt', self._max_score))

        task_parsed_xml = task_descriptor.definition_from_xml(etree_xml, self.system)
        task = children['modules'][task_type](self.system, self.location, task_parsed_xml, task_descriptor,
                                              self.static_data, instance_state=task_state)
        last_response = task.latest_answer()
        last_score = task.latest_score()
        all_scores = task.all_scores()
        last_post_assessment = task.latest_post_assessment(self.system)
        last_post_feedback = ""
        feedback_dicts = [{}]
        grader_ids = [0]
        submission_ids = [0]
        if task_type == "openended":
            last_post_assessment = task.latest_post_assessment(self.system, short_feedback=False, join_feedback=False)
            if isinstance(last_post_assessment, list):
                eval_list = []
                for assess in last_post_assessment:
                    eval_list.append(task.format_feedback_with_evaluation(self.system, assess))
                last_post_evaluation = "".join(eval_list)
            else:
                last_post_evaluation = task.format_feedback_with_evaluation(self.system, last_post_assessment)
            last_post_assessment = last_post_evaluation
            try:
                rubric_data = task._parse_score_msg(task.child_history[-1].get('post_assessment', "{}"), self.system)
            except Exception:
                log.debug("Could not parse rubric data from child history.  "
                          "Likely we have not yet initialized a previous step, so this is perfectly fine.")
                rubric_data = {}
            rubric_scores = rubric_data.get('rubric_scores')
            grader_types = rubric_data.get('grader_types')
            feedback_items = rubric_data.get('feedback_items')
            feedback_dicts = rubric_data.get('feedback_dicts')
            grader_ids = rubric_data.get('grader_ids')
            submission_ids = rubric_data.get('submission_ids')
        elif task_type == "selfassessment":
            rubric_scores = last_post_assessment
            grader_types = ['SA']
            feedback_items = ['']
            last_post_assessment = ""
        last_correctness = task.is_last_response_correct()
        max_score = task.max_score()
        state = task.child_state
        if task_type in HUMAN_TASK_TYPE:
            human_task_name = HUMAN_TASK_TYPE[task_type]
        else:
            human_task_name = task_type

        if state in task.HUMAN_NAMES:
            human_state = task.HUMAN_NAMES[state]
        else:
            human_state = state
        if grader_types is not None and len(grader_types) > 0:
            grader_type = grader_types[0]
        else:
            grader_type = "IN"
            grader_types = ["IN"]

        if grader_type in HUMAN_GRADER_TYPE:
            human_grader_name = HUMAN_GRADER_TYPE[grader_type]
        else:
            human_grader_name = grader_type

        last_response_dict = {
            'response': last_response,
            'score': last_score,
            'all_scores': all_scores,
            'post_assessment': last_post_assessment,
            'type': task_type,
            'max_score': max_score,
            'state': state,
            'human_state': human_state,
            'human_task': human_task_name,
            'correct': last_correctness,
            'min_score_to_attempt': min_score_to_attempt,
            'max_score_to_attempt': max_score_to_attempt,
            'rubric_scores': rubric_scores,
            'grader_types': grader_types,
            'feedback_items': feedback_items,
            'grader_type': grader_type,
            'human_grader_type': human_grader_name,
            'feedback_dicts': feedback_dicts,
            'grader_ids': grader_ids,
            'submission_ids': submission_ids,
            'success': True
        }
        return last_response_dict

    def extract_human_name_from_task(self, task_xml):
        """
        Given the xml for a task, pull out the human name for it.
        Input: xml string
        Output: a human readable task name (ie Self Assessment)
        """
        tree = etree.fromstring(task_xml)
        payload = tree.xpath("/openended/openendedparam/grader_payload")
        if len(payload) == 0:
            task_name = "selfassessment"
        else:
            inner_payload = json.loads(payload[0].text)
            task_name = inner_payload['grader_settings']

        human_task = HUMAN_TASK_TYPE[task_name]
        return human_task

    def update_task_states(self):
        """
        Updates the task state of the combined open ended module with the task state of the current child module.
        Input: None
        Output: boolean indicating whether or not the task state changed.
        """
        changed = False
        if not self.ready_to_reset:
            self.task_states[self.current_task_number] = self.current_task.get_instance_state()
            current_task_state = json.loads(self.task_states[self.current_task_number])
            if current_task_state['child_state'] == self.DONE:
                self.current_task_number += 1
                if self.current_task_number >= (len(self.task_xml)):
                    self.state = self.DONE
                    self.current_task_number = len(self.task_xml) - 1
                else:
                    self.state = self.INITIAL
                changed = True
                self.setup_next_task()
        return changed

    def update_task_states_ajax(self, return_html):
        """
        Runs the update task states function for ajax calls.  Currently the same as update_task_states
        Input: The html returned by the handle_ajax function of the child
        Output: New html that should be rendered
        """
        changed = self.update_task_states()
        if changed:
            pass
        return return_html

    def check_if_student_has_done_needed_grading(self):
        """
        Checks with the ORA server to see if the student has completed the needed peer grading to be shown their grade.
        For example, if a student submits one response, and three peers grade their response, the student
        cannot see their grades and feedback unless they reciprocate.
        Output:
        success - boolean indicator of success
        allowed_to_submit - boolean indicator of whether student has done their needed grading or not
        error_message - If not success, explains why
        """
        student_id = self.system.anonymous_student_id
        success = False
        allowed_to_submit = True
        try:
            response = self.peer_gs.get_data_for_location(self.location, student_id)
            count_graded = response['count_graded']
            count_required = response['count_required']
            student_sub_count = response['student_sub_count']
            count_available = response['count_available']
            success = True
        except GradingServiceError:
            # This is a dev_facing_error
            log.error("Could not contact external open ended graders for location {0} and student {1}".format(
                self.location, student_id))
            # This is a student_facing_error
            error_message = "Could not contact the graders.  Please notify course staff."
            return success, allowed_to_submit, error_message
        except KeyError:
            log.error("Invalid response from grading server for location {0} and student {1}".format(self.location, student_id))
            error_message = "Received invalid response from the graders.  Please notify course staff."
            return success, allowed_to_submit, error_message
        if count_graded >= count_required or count_available == 0:
            error_message = ""
            return success, allowed_to_submit, error_message
        else:
            allowed_to_submit = False
            # This is a student_facing_error
            error_string = ("<h4>Feedback not available yet</h4>"
                            "<p>You need to peer grade {0} more submissions in order to see your feedback.</p>"
                            "<p>You have graded responses from {1} students, and {2} students have graded your submissions. </p>"
                            "<p>You have made {3} submissions.</p>")
            error_message = error_string.format(count_required - count_graded, count_graded, count_required,
                                                student_sub_count)
            return success, allowed_to_submit, error_message

    def get_rubric(self, _data):
        """
        Gets the results of a given grader via ajax.
        Input: AJAX data dictionary
        Output: Dictionary to be rendered via ajax that contains the result html.
        """
        ugettext = self.system.service(self, "i18n").ugettext
        all_responses = []
        success, can_see_rubric, error = self.check_if_student_has_done_needed_grading()
        if not can_see_rubric:
            return {
                'html': self.system.render_template(
                    '{0}/combined_open_ended_hidden_results.html'.format(self.TEMPLATE_DIR),
                    {'error': error}),
                'success': True,
                'hide_reset': True
            }

        contexts = []
        rubric_number = self.current_task_number
        if self.ready_to_reset:
            rubric_number += 1
        response = self.get_last_response(rubric_number)
        score_length = len(response['grader_types'])
        for z in xrange(score_length):
            if response['grader_types'][z] in HUMAN_GRADER_TYPE:
                try:
                    feedback = response['feedback_dicts'][z].get('feedback', '')
                except TypeError:
                    return {'success': False}
                rubric_scores = [[response['rubric_scores'][z]]]
                grader_types = [[response['grader_types'][z]]]
                feedback_items = [[response['feedback_items'][z]]]
                rubric_html = self.rubric_renderer.render_combined_rubric(
                    stringify_children(self.static_data['rubric']),
                    rubric_scores,
                    grader_types,
                    feedback_items
                )
                contexts.append({
                    'result': rubric_html,
                    # Translators: "Scored rubric" appears to a user as part of a longer
                    # string that looks something like: "Scored rubric from grader 1".
                    # "Scored" is an adjective that modifies the noun "rubric".
                    # That longer string appears when a user is viewing a graded rubric
                    # returned from one of the graders of their openended response problem.
                    'task_name': ugettext('Scored rubric'),
                    'feedback': feedback
                })

        context = {
            'results': contexts,
        }
        html = self.system.render_template('{0}/combined_open_ended_results.html'.format(self.TEMPLATE_DIR), context)
        return {'html': html, 'success': True, 'hide_reset': False}

    def get_legend(self, _data):
        """
        Gets the results of a given grader via ajax.
        Input: AJAX data dictionary
        Output: Dictionary to be rendered via ajax that contains the result html.
        """
        context = {
            'legend_list': LEGEND_LIST,
        }
        html = self.system.render_template('{0}/combined_open_ended_legend.html'.format(self.TEMPLATE_DIR), context)
        return {'html': html, 'success': True}

    def handle_ajax(self, dispatch, data):
        """
        This is called by courseware.module_render, to handle an AJAX call.
        "data" is request.POST.

        Returns a json dictionary:
        { 'progress_changed' : True/False,
        'progress': 'none'/'in_progress'/'done',
        <other request-specific values here > }
        """

        handlers = {
            'next_problem': self.next_problem,
            'reset': self.reset,
            'get_combined_rubric': self.get_rubric,
            'get_legend': self.get_legend,
            'get_last_response': self.get_last_response_ajax,
            'get_current_state': self.get_current_state,
            'get_html': self.get_html_ajax,
        }

        if dispatch not in handlers:
            return_html = self.current_task.handle_ajax(dispatch, data, self.system)
            return self.update_task_states_ajax(return_html)

        d = handlers[dispatch](data)
        return json.dumps(d, cls=ComplexEncoder)

    def get_current_state(self, data):
        """
        Gets the current state of the module.
        """
        return self.get_context()

    def get_last_response_ajax(self, data):
        """
        Get the last response via ajax callback
        data - Needed to preserve ajax callback structure
        Output: Last response dictionary
        """
        return self.get_last_response(self.current_task_number)

    def next_problem(self, _data):
        """
        Called via ajax to advance to the next problem.
        Input: AJAX data request.
        Output: Dictionary to be rendered
        """
        self.update_task_states()
        return {'success': True, 'html': self.get_html_nonsystem(), 'allow_reset': self.ready_to_reset}

    def reset(self, data):
        """
        If resetting is allowed, reset the state of the combined open ended module.
        Input: AJAX data dictionary
        Output: AJAX dictionary to tbe rendered
        """
        ugettext = self.system.service(self, "i18n").ugettext
        if self.state != self.DONE:
            if not self.ready_to_reset:
                return self.out_of_sync_error(data)
        success, can_reset, error = self.check_if_student_has_done_needed_grading()
        if not can_reset:
            return {'error': error, 'success': False}
        if self.student_attempts >= self.max_attempts - 1:
            if self.student_attempts == self.max_attempts - 1:
                self.student_attempts += 1
            return {
                'success': False,
                # This is a student_facing_error
                'error': ugettext(
                    'You have attempted this question {number_of_student_attempts} times. '
                    'You are only allowed to attempt it {max_number_of_attempts} times.'
                ).format(
                    number_of_student_attempts=self.student_attempts,
                    max_number_of_attempts=self.max_attempts
                )
            }
        self.student_attempts += 1
        self.state = self.INITIAL
        self.ready_to_reset = False
        for i in xrange(len(self.task_xml)):
            self.current_task_number = i
            self.setup_next_task(reset=True)
            self.current_task.reset(self.system)
            self.task_states[self.current_task_number] = self.current_task.get_instance_state()
        self.current_task_number = 0
        self.ready_to_reset = False

        self.setup_next_task()
        return {'success': True, 'html': self.get_html_nonsystem()}

    def get_instance_state(self):
        """
        Returns the current instance state.  The module can be recreated from the instance state.
        Input: None
        Output: A dictionary containing the instance state.
        """

        state = {
            'version': self.STATE_VERSION,
            'current_task_number': self.current_task_number,
            'state': self.state,
            'task_states': self.task_states,
            'student_attempts': self.student_attempts,
            'ready_to_reset': self.ready_to_reset,
        }

        return json.dumps(state)

    def get_status(self, render_via_ajax):
        """
        Gets the status panel to be displayed at the top right.
        Input: None
        Output: The status html to be rendered
        """
        ugettext = self.system.service(self, "i18n").ugettext
        status_list = []
        current_task_human_name = ""
        for i in xrange(len(self.task_xml)):
            human_task_name = self.extract_human_name_from_task(self.task_xml[i])
            human_task_name = ugettext(human_task_name)    # pylint: disable=translation-of-non-string
            # Extract the name of the current task for screen readers.
            if self.current_task_number == i:
                current_task_human_name = human_task_name
            task_data = {
                'task_number': i + 1,
                'human_task': human_task_name,
                'current': self.current_task_number == i
            }
            status_list.append(task_data)

        context = {
            'status_list': status_list,
            'grader_type_image_dict': GRADER_TYPE_IMAGE_DICT,
            'legend_list': LEGEND_LIST,
            'render_via_ajax': render_via_ajax,
            'current_task_human_name': current_task_human_name,
        }
        status_html = self.system.render_template(
            "{0}/combined_open_ended_status.html".format(self.TEMPLATE_DIR), context
        )

        return status_html

    def check_if_done_and_scored(self):
        """
        Checks if the object is currently in a finished state (either student didn't meet criteria to move
        to next step, in which case they are in the allow_reset state, or they are done with the question
        entirely, in which case they will be in the self.DONE state), and if it is scored or not.
        @return: Boolean corresponding to the above.
        """
        return (self.state == self.DONE or self.ready_to_reset) and self.is_scored

    def get_weight(self):
        """
        Return the weight of the problem.  The old default weight was None, so set to 1 in that case.
        Output - int weight
        """
        weight = self.weight
        if weight is None:
            weight = 1
        return weight

    def get_score(self):
        """
        Score the student received on the problem, or None if there is no
        score.

        Returns:
          dictionary
             {'score': integer, from 0 to get_max_score(),
              'total': get_max_score()}
        """
        max_score = None
        score = None

        #The old default was None, so set to 1 if it is the old default weight
        weight = self.get_weight()
        if self.is_scored:
            # Finds the maximum score of all student attempts and keeps it.
            score_mat = []
            for i in xrange(len(self.task_states)):
                # For each task, extract all student scores on that task (each attempt for each task)
                last_response = self.get_last_response(i)
                score = last_response.get('all_scores', None)
                if score is not None:
                    # Convert none scores and weight scores properly
                    for j in xrange(len(score)):
                        if score[j] is None:
                            score[j] = 0
                        score[j] *= float(weight)
                    score_mat.append(score)

            if len(score_mat) > 0:
                # Currently, assume that the final step is the correct one, and that those are the final scores.
                # This will change in the future, which is why the machinery above exists to extract all scores on all steps
                scores = score_mat[-1]
                score = max(scores)
            else:
                score = 0

            if self._max_score is not None:
                # Weight the max score if it is not None
                max_score = self._max_score * float(weight)
            else:
                # Without a max_score, we cannot have a score!
                score = None

        score_dict = {
            'score': score,
            'total': max_score,
        }

        return score_dict

    def max_score(self):
        """
        Maximum score possible in this module.  Returns the max score if finished, None if not.
        """
        max_score = None
        if self.check_if_done_and_scored():
            max_score = self._max_score
        return max_score

    def get_progress(self):
        """
        Generate a progress object. Progress objects represent how far the
        student has gone in this module.  Must be implemented to get correct
        progress tracking behavior in nested modules like sequence and
        vertical.  This behavior is consistent with capa.

        If the module is unscored, return None (consistent with capa).
        """

        d = self.get_score()

        if d['total'] > 0 and self.is_scored:

            try:
                return Progress(d['score'], d['total'])
            except (TypeError, ValueError):
                log.exception("Got bad progress")
                return None

        return None

    def out_of_sync_error(self, data, msg=''):
        """
        return dict out-of-sync error message, and also log.
        """
        ugettext = self.system.service(self, "i18n").ugettext
        #This is a dev_facing_error
        log.warning(
            "Combined module state out sync. state: %r, data: %r. %s",
            self.state,
            data,
            msg
        )
        #This is a student_facing_error
        return {
            'success': False,
            'error': ugettext('The problem state got out-of-sync. Please try reloading the page.')
        }

    @classmethod
    def service_declaration(cls, service_name):
        """
        This classmethod is copied from XBlock's service_declaration.
        It is included to make this class act enough like an XBlock
        to get i18n working on it.

        This is currently only used for i18n, and will return "need"
        in that case.

        Arguments:
            service_name (string): the name of the service requested.

        Returns:
            One of "need", "want", or None.

        """
        declaration = cls._combined_services.get(service_name)
        return declaration


class CombinedOpenEndedV1Descriptor(object):
    """
    Module for adding combined open ended questions
    """
    mako_template = "widgets/html-edit.html"
    module_class = CombinedOpenEndedV1Module
    filename_extension = "xml"

    has_score = True

    def __init__(self, system):
        self.system = system

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Pull out the individual tasks, the rubric, and the prompt, and parse

        Returns:
        {
        'rubric': 'some-html',
        'prompt': 'some-html',
        'task_xml': dictionary of xml strings,
        }
        """
        expected_children = ['task', 'rubric', 'prompt']
        for child in expected_children:
            if len(xml_object.xpath(child)) == 0:
                # This is a staff_facing_error
                raise ValueError(
                    u"Combined Open Ended definition must include at least one '{0}' tag. Contact the learning sciences group for assistance. {1}".format(
                        child, xml_object))

        def parse_task(k):
            """Assumes that xml_object has child k"""
            return [stringify_children(xml_object.xpath(k)[i]) for i in xrange(len(xml_object.xpath(k)))]

        def parse(k):
            """Assumes that xml_object has child k"""
            return xml_object.xpath(k)[0]

        return {'task_xml': parse_task('task'), 'prompt': parse('prompt'), 'rubric': parse('rubric')}

    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        elt = etree.Element('combinedopenended')

        def add_child(k):
            child_str = u'<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in ['task']:
            add_child(child)

        return elt
