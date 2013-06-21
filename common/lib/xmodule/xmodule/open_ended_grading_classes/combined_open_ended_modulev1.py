import json
import logging
from lxml import etree
from xmodule.timeinfo import TimeInfo
from xmodule.capa_module import ComplexEncoder
from xmodule.progress import Progress
from xmodule.stringify import stringify_children
import self_assessment_module
import open_ended_module
from .combined_open_ended_rubric import CombinedOpenEndedRubric, GRADER_TYPE_IMAGE_DICT, HUMAN_GRADER_TYPE, LEGEND_LIST

log = logging.getLogger("mitx.courseware")

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

HUMAN_TASK_TYPE = {
    'selfassessment': "Self Assessment",
    'openended': "edX Assessment",
}

# Default value that controls whether or not to skip basic spelling checks in the controller
# Metadata overrides this
SKIP_BASIC_CHECKS = False


class CombinedOpenEndedV1Module():
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

    # Where the templates live for this problem
    TEMPLATE_DIR = "combinedopenended"

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, metadata=None, static_data=None, **kwargs):

        """
        Definition file should have one or many task blocks, a rubric block, and a prompt block:

        Sample file:
        <combinedopenended attempts="10000">
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

        self.instance_state = instance_state
        self.display_name = instance_state.get('display_name', "Open Ended")

        # We need to set the location here so the child modules can use it
        system.set('location', location)
        self.system = system

        # Tells the system which xml definition to load
        self.current_task_number = instance_state.get('current_task_number', 0)
        # This loads the states of the individual children
        self.task_states = instance_state.get('task_states', [])
        # Overall state of the combined open ended module
        self.state = instance_state.get('state', self.INITIAL)

        self.student_attempts = instance_state.get('student_attempts', 0)
        self.weight = instance_state.get('weight', 1)

        # Allow reset is true if student has failed the criteria to move to the next child task
        self.ready_to_reset = instance_state.get('ready_to_reset', False)
        self.attempts = self.instance_state.get('attempts', MAX_ATTEMPTS)
        self.is_scored = self.instance_state.get('is_graded', IS_SCORED) in TRUE_DICT
        self.accept_file_upload = self.instance_state.get('accept_file_upload', ACCEPT_FILE_UPLOAD) in TRUE_DICT
        self.skip_basic_checks = self.instance_state.get('skip_spelling_checks', SKIP_BASIC_CHECKS) in TRUE_DICT

        due_date = self.instance_state.get('due', None)

        grace_period_string = self.instance_state.get('graceperiod', None)
        try:
            self.timeinfo = TimeInfo(due_date, grace_period_string)
        except Exception:
            log.error("Error parsing due date information in location {0}".format(location))
            raise
        self.display_due_date = self.timeinfo.display_due_date

        self.rubric_renderer = CombinedOpenEndedRubric(system, True)
        rubric_string = stringify_children(definition['rubric'])
        self._max_score = self.rubric_renderer.check_if_rubric_is_parseable(rubric_string, location, MAX_SCORE_ALLOWED)

        # Static data is passed to the child modules to render
        self.static_data = {
            'max_score': self._max_score,
            'max_attempts': self.attempts,
            'prompt': definition['prompt'],
            'rubric': definition['rubric'],
            'display_name': self.display_name,
            'accept_file_upload': self.accept_file_upload,
            'close_date': self.timeinfo.close_date,
            's3_interface': self.system.s3_interface,
            'skip_basic_checks': self.skip_basic_checks,
        }

        self.task_xml = definition['task_xml']
        self.location = location
        self.setup_next_task()

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

                if (current_response_data['min_score_to_attempt'] > last_response_data['score']
                    or current_response_data['max_score_to_attempt'] < last_response_data['score']):
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

        context = {
            'items': [{'content': task_html}],
            'ajax_url': self.system.ajax_url,
            'allow_reset': self.ready_to_reset,
            'state': self.state,
            'task_count': len(self.task_xml),
            'task_number': self.current_task_number + 1,
            'status': self.get_status(False),
            'display_name': self.display_name,
            'accept_file_upload': self.accept_file_upload,
            'location': self.location,
            'legend_list': LEGEND_LIST,
        }

        return context

    def get_html(self):
        """
        Gets HTML for rendering.
        Input: None
        Output: rendered html
        """
        context = self.get_context()
        html = self.system.render_template('{0}/combined_open_ended.html'.format(self.TEMPLATE_DIR), context)
        return html

    def get_html_nonsystem(self):
        """
        Gets HTML for rendering via AJAX.  Does not use system, because system contains some additional
        html, which is not appropriate for returning via ajax calls.
        Input: None
        Output: HTML rendered directly via Mako
        """
        context = self.get_context()
        html = self.system.render_template('{0}/combined_open_ended.html'.format(self.TEMPLATE_DIR), context)
        return html

    def get_html_base(self):
        """
        Gets the HTML associated with the current child task
        Input: None
        Output: Child task HTML
        """
        self.update_task_states()
        return self.current_task.get_html(self.system)

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
                for i in xrange(0, len(last_post_assessment)):
                    eval_list.append(task.format_feedback_with_evaluation(self.system, last_post_assessment[i]))
                last_post_evaluation = "".join(eval_list)
            else:
                last_post_evaluation = task.format_feedback_with_evaluation(self.system, last_post_assessment)
            last_post_assessment = last_post_evaluation
            try:
                rubric_data = task._parse_score_msg(task.child_history[-1].get('post_assessment', ""), self.system)
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
        }
        return last_response_dict

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

    def get_rubric(self, get):
        """
        Gets the results of a given grader via ajax.
        Input: AJAX get dictionary
        Output: Dictionary to be rendered via ajax that contains the result html.
        """
        all_responses = []
        loop_up_to_task = self.current_task_number + 1
        for i in xrange(0, loop_up_to_task):
            all_responses.append(self.get_last_response(i))
        rubric_scores = [all_responses[i]['rubric_scores'] for i in xrange(0, len(all_responses)) if
                         len(all_responses[i]['rubric_scores']) > 0 and all_responses[i]['grader_types'][
                             0] in HUMAN_GRADER_TYPE.keys()]
        grader_types = [all_responses[i]['grader_types'] for i in xrange(0, len(all_responses)) if
                        len(all_responses[i]['grader_types']) > 0 and all_responses[i]['grader_types'][
                            0] in HUMAN_GRADER_TYPE.keys()]
        feedback_items = [all_responses[i]['feedback_items'] for i in xrange(0, len(all_responses)) if
                          len(all_responses[i]['feedback_items']) > 0 and all_responses[i]['grader_types'][
                              0] in HUMAN_GRADER_TYPE.keys()]
        rubric_html = self.rubric_renderer.render_combined_rubric(stringify_children(self.static_data['rubric']),
                                                                  rubric_scores,
                                                                  grader_types, feedback_items)

        response_dict = all_responses[-1]
        context = {
            'results': rubric_html,
            'task_name': 'Scored Rubric',
            'class_name': 'combined-rubric-container'
        }
        html = self.system.render_template('{0}/combined_open_ended_results.html'.format(self.TEMPLATE_DIR), context)
        return {'html': html, 'success': True}

    def get_legend(self, get):
        """
        Gets the results of a given grader via ajax.
        Input: AJAX get dictionary
        Output: Dictionary to be rendered via ajax that contains the result html.
        """
        context = {
            'legend_list': LEGEND_LIST,
        }
        html = self.system.render_template('{0}/combined_open_ended_legend.html'.format(self.TEMPLATE_DIR), context)
        return {'html': html, 'success': True}

    def get_results(self, get):
        """
        Gets the results of a given grader via ajax.
        Input: AJAX get dictionary
        Output: Dictionary to be rendered via ajax that contains the result html.
        """
        self.update_task_states()
        loop_up_to_task = self.current_task_number + 1
        all_responses = []
        for i in xrange(0, loop_up_to_task):
            all_responses.append(self.get_last_response(i))
        context_list = []
        for ri in all_responses:
            for i in xrange(0, len(ri['rubric_scores'])):
                feedback = ri['feedback_dicts'][i].get('feedback', '')
                rubric_data = self.rubric_renderer.render_rubric(stringify_children(self.static_data['rubric']),
                                                                 ri['rubric_scores'][i])
                if rubric_data['success']:
                    rubric_html = rubric_data['html']
                else:
                    rubric_html = ''
                context = {
                    'rubric_html': rubric_html,
                    'grader_type': ri['grader_type'],
                    'feedback': feedback,
                    'grader_id': ri['grader_ids'][i],
                    'submission_id': ri['submission_ids'][i],
                }
                context_list.append(context)
        feedback_table = self.system.render_template('{0}/open_ended_result_table.html'.format(self.TEMPLATE_DIR), {
            'context_list': context_list,
            'grader_type_image_dict': GRADER_TYPE_IMAGE_DICT,
            'human_grader_types': HUMAN_GRADER_TYPE,
            'rows': 50,
            'cols': 50,
        })
        context = {
            'results': feedback_table,
            'task_name': "Feedback",
            'class_name': "result-container",
        }
        html = self.system.render_template('{0}/combined_open_ended_results.html'.format(self.TEMPLATE_DIR), context)
        return {'html': html, 'success': True}

    def get_status_ajax(self, get):
        """
        Gets the results of a given grader via ajax.
        Input: AJAX get dictionary
        Output: Dictionary to be rendered via ajax that contains the result html.
        """
        html = self.get_status(True)
        return {'html': html, 'success': True}

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
            'get_results': self.get_results,
            'get_combined_rubric': self.get_rubric,
            'get_status': self.get_status_ajax,
            'get_legend': self.get_legend,
        }

        if dispatch not in handlers:
            return_html = self.current_task.handle_ajax(dispatch, get, self.system)
            return self.update_task_states_ajax(return_html)

        d = handlers[dispatch](get)
        return json.dumps(d, cls=ComplexEncoder)

    def next_problem(self, get):
        """
        Called via ajax to advance to the next problem.
        Input: AJAX get request.
        Output: Dictionary to be rendered
        """
        self.update_task_states()
        return {'success': True, 'html': self.get_html_nonsystem(), 'allow_reset': self.ready_to_reset}

    def reset(self, get):
        """
        If resetting is allowed, reset the state of the combined open ended module.
        Input: AJAX get dictionary
        Output: AJAX dictionary to tbe rendered
        """
        if self.state != self.DONE:
            if not self.ready_to_reset:
                return self.out_of_sync_error(get)

        if self.student_attempts > self.attempts:
            return {
                'success': False,
                #This is a student_facing_error
                'error': (
                    'You have attempted this question {0} times.  '
                    'You are only allowed to attempt it {1} times.'
                ).format(self.student_attempts, self.attempts)
            }
        self.state = self.INITIAL
        self.ready_to_reset = False
        for i in xrange(0, len(self.task_xml)):
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
        status = []
        for i in xrange(0, self.current_task_number + 1):
            task_data = self.get_last_response(i)
            task_data.update({'task_number': i + 1})
            status.append(task_data)

        context = {
            'status_list': status,
            'grader_type_image_dict': GRADER_TYPE_IMAGE_DICT,
            'legend_list': LEGEND_LIST,
            'render_via_ajax': render_via_ajax,
        }
        status_html = self.system.render_template("{0}/combined_open_ended_status.html".format(self.TEMPLATE_DIR),
                                                  context)

        return status_html

    def check_if_done_and_scored(self):
        """
        Checks if the object is currently in a finished state (either student didn't meet criteria to move
        to next step, in which case they are in the allow_reset state, or they are done with the question
        entirely, in which case they will be in the self.DONE state), and if it is scored or not.
        @return: Boolean corresponding to the above.
        """
        return (self.state == self.DONE or self.ready_to_reset) and self.is_scored

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
        if self.is_scored and self.weight is not None:
            # Finds the maximum score of all student attempts and keeps it.
            score_mat = []
            for i in xrange(0, len(self.task_states)):
                # For each task, extract all student scores on that task (each attempt for each task)
                last_response = self.get_last_response(i)
                max_score = last_response.get('max_score', None)
                score = last_response.get('all_scores', None)
                if score is not None:
                    # Convert none scores and weight scores properly
                    for z in xrange(0, len(score)):
                        if score[z] is None:
                            score[z] = 0
                        score[z] *= float(self.weight)
                    score_mat.append(score)

            if len(score_mat) > 0:
                # Currently, assume that the final step is the correct one, and that those are the final scores.
                # This will change in the future, which is why the machinery above exists to extract all scores on all steps
                # TODO: better final score handling.
                scores = score_mat[-1]
                score = max(scores)
            else:
                score = 0

            if max_score is not None:
                # Weight the max score if it is not None
                max_score *= float(self.weight)
            else:
                # Without a max_score, we cannot have a score!
                score = None

        score_dict = {
            'score': score,
            'total': max_score,
        }

        return score_dict

    def max_score(self):
        ''' Maximum score. Two notes:

            * This is generic; in abstract, a problem could be 3/5 points on one
              randomization, and 5/7 on another
        '''
        max_score = None
        if self.check_if_done_and_scored():
            last_response = self.get_last_response(self.current_task_number)
            max_score = last_response['max_score']
        return max_score

    def get_progress(self):
        ''' Return a progress.Progress object that represents how far the
        student has gone in this module.  Must be implemented to get correct
        progress tracking behavior in nesting modules like sequence and
        vertical.

        If this module has no notion of progress, return None.
        '''
        progress_object = Progress(self.current_task_number, len(self.task_xml))

        return progress_object

    def out_of_sync_error(self, get, msg=''):
        """
        return dict out-of-sync error message, and also log.
        """
        #This is a dev_facing_error
        log.warning("Combined module state out sync. state: %r, get: %r. %s",
                    self.state, get, msg)
        #This is a student_facing_error
        return {'success': False,
                'error': 'The problem state got out-of-sync.  Please try reloading the page.'}


class CombinedOpenEndedV1Descriptor():
    """
    Module for adding combined open ended questions
    """
    mako_template = "widgets/html-edit.html"
    module_class = CombinedOpenEndedV1Module
    filename_extension = "xml"

    has_score = True
    template_dir_name = "combinedopenended"

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
                    "Combined Open Ended definition must include at least one '{0}' tag. Contact the learning sciences group for assistance. {1}".format(
                        child, xml_object))

        def parse_task(k):
            """Assumes that xml_object has child k"""
            return [stringify_children(xml_object.xpath(k)[i]) for i in xrange(0, len(xml_object.xpath(k)))]

        def parse(k):
            """Assumes that xml_object has child k"""
            return xml_object.xpath(k)[0]

        return {'task_xml': parse_task('task'), 'prompt': parse('prompt'), 'rubric': parse('rubric')}


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
