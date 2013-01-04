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
import hashlib
import capa.xqueue_interface as xqueue_interface

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

class OpenEndedModule():
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

    DEFAULT_QUEUE = 'open-ended'
    DEFAULT_MESSAGE_QUEUE = 'open-ended-message'
    max_inputfields = 1

    STATE_VERSION = 1

    # states
    INITIAL = 'initial'
    ASSESSING = 'assessing'
    POST_ASSESSMENT = 'post_assessment'
    DONE = 'done'

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
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
        self.max_attempts = int(instance_state.get('attempts', MAX_ATTEMPTS))

        # Used for progress / grading.  Currently get credit just for
        # completion (doesn't matter if you self-assessed correct/incorrect).
        self._max_score = int(instance_state.get('max_score', MAX_SCORE))

        oeparam = definition['openendedparam']
        prompt = definition['prompt']
        rubric = definition['rubric']

        self.url = definition.get('url', None)
        self.queue_name = definition.get('queuename', self.DEFAULT_QUEUE)
        self.message_queue_name = definition.get('message-queuename', self.DEFAULT_MESSAGE_QUEUE)

        #This is needed to attach feedback to specific responses later
        self.submission_id=None
        self.grader_id=None

        if oeparam is None:
            raise ValueError("No oeparam found in problem xml.")
        if prompt is None:
            raise ValueError("No prompt found in problem xml.")
        if rubric is None:
            raise ValueError("No rubric found in problem xml.")

        self._parse(oeparam, prompt, rubric)

    def _parse(self, oeparam, prompt, rubric):
        '''
        Parse OpenEndedResponse XML:
            self.initial_display
            self.payload - dict containing keys --
            'grader' : path to grader settings file, 'problem_id' : id of the problem

            self.answer - What to display when show answer is clicked
        '''
        # Note that OpenEndedResponse is agnostic to the specific contents of grader_payload
        prompt_string = self.stringify_children(prompt)
        rubric_string = self.stringify_children(rubric)

        grader_payload = oeparam.find('grader_payload')
        grader_payload = grader_payload.text if grader_payload is not None else ''

        #Update grader payload with student id.  If grader payload not json, error.
        try:
            parsed_grader_payload = json.loads(grader_payload)
            # NOTE: self.system.location is valid because the capa_module
            # __init__ adds it (easiest way to get problem location into
            # response types)
        except TypeError, ValueError:
            log.exception("Grader payload %r is not a json object!", grader_payload)

        self.initial_display = find_with_default(oeparam, 'initial_display', '')
        self.answer = find_with_default(oeparam, 'answer_display', 'No answer given.')

        parsed_grader_payload.update({
            'location' : self.system.location,
            'course_id' : self.system.course_id,
            'prompt' : prompt_string,
            'rubric' : rubric_string,
            'initial_display' : self.initial_display,
            'answer' : self.answer,
            })
        updated_grader_payload = json.dumps(parsed_grader_payload)

        self.payload = {'grader_payload': updated_grader_payload}

        try:
            self.max_score = int(find_with_default(oeparam, 'max_score', 1))
        except ValueError:
            self.max_score = 1

    def handle_message_post(self,get):
        """
        Handles a student message post (a reaction to the grade they received from an open ended grader type)
        Returns a boolean success/fail and an error message
        """

        event_info = dict()
        event_info['problem_id'] = self.location.url()
        event_info['student_id'] = self.system.anonymous_student_id
        event_info['survey_responses']= get

        survey_responses=event_info['survey_responses']
        for tag in ['feedback', 'submission_id', 'grader_id', 'score']:
            if tag not in survey_responses:
                return False, "Could not find needed tag {0}".format(tag)
        try:
            submission_id=int(survey_responses['submission_id'])
            grader_id = int(survey_responses['grader_id'])
            feedback = str(survey_responses['feedback'].encode('ascii', 'ignore'))
            score = int(survey_responses['score'])
        except:
            error_message=("Could not parse submission id, grader id, "
                           "or feedback from message_post ajax call.  Here is the message data: {0}".format(survey_responses))
            log.exception(error_message)
            return False, "There was an error saving your feedback.  Please contact course staff."

        qinterface = self.system.xqueue['interface']
        qtime = datetime.strftime(datetime.now(), xqueue_interface.dateformat)
        anonymous_student_id = self.system.anonymous_student_id
        queuekey = xqueue_interface.make_hashkey(str(self.system.seed) + qtime +
                                                 anonymous_student_id +
                                                 self.answer_id)

        xheader = xqueue_interface.make_xheader(
            lms_callback_url=self.system.xqueue['callback_url'],
            lms_key=queuekey,
            queue_name=self.message_queue_name
        )

        student_info = {'anonymous_student_id': anonymous_student_id,
                        'submission_time': qtime,
                        }
        contents= {
            'feedback' : feedback,
            'submission_id' : submission_id,
            'grader_id' : grader_id,
            'score': score,
            'student_info' : json.dumps(student_info),
            }

        (error, msg) = qinterface.send_to_queue(header=xheader,
            body=json.dumps(contents))

        #Convert error to a success value
        success=True
        if error:
            success=False

        return success, "Successfully submitted your feedback."

    def get_score(self, student_answers):
        try:
            submission = student_answers[self.answer_id]
        except KeyError:
            msg = ('Cannot get student answer for answer_id: {0}. student_answers {1}'
                   .format(self.answer_id, student_answers))
            log.exception(msg)
            raise LoncapaProblemError(msg)

        # Prepare xqueue request
        #------------------------------------------------------------

        qinterface = self.system.xqueue['interface']
        qtime = datetime.strftime(datetime.now(), xqueue_interface.dateformat)

        anonymous_student_id = self.system.anonymous_student_id

        # Generate header
        queuekey = xqueue_interface.make_hashkey(str(self.system.seed) + qtime +
                                                 anonymous_student_id +
                                                 self.answer_id)

        xheader = xqueue_interface.make_xheader(lms_callback_url=self.system.xqueue['callback_url'],
            lms_key=queuekey,
            queue_name=self.queue_name)

        self.context.update({'submission': submission})

        contents = self.payload.copy()

        # Metadata related to the student submission revealed to the external grader
        student_info = {'anonymous_student_id': anonymous_student_id,
                        'submission_time': qtime,
                        }

        #Update contents with student response and student info
        contents.update({
            'student_info': json.dumps(student_info),
            'student_response': submission,
            'max_score' : self.max_score,
            })

        # Submit request. When successful, 'msg' is the prior length of the queue
        (error, msg) = qinterface.send_to_queue(header=xheader,
            body=json.dumps(contents))

        # State associated with the queueing request
        queuestate = {'key': queuekey,
                      'time': qtime,}

        cmap = CorrectMap()
        if error:
            cmap.set(self.answer_id, queuestate=None,
                msg='Unable to deliver your submission to grader. (Reason: {0}.)'
                    ' Please try again later.'.format(msg))
        else:
            # Queueing mechanism flags:
            #   1) Backend: Non-null CorrectMap['queuestate'] indicates that
            #      the problem has been queued
            #   2) Frontend: correctness='incomplete' eventually trickles down
            #      through inputtypes.textbox and .filesubmission to inform the
            #      browser that the submission is queued (and it could e.g. poll)
            cmap.set(self.answer_id, queuestate=queuestate,
                correctness='incomplete', msg=msg)

        return cmap

    def _update_score(self, score_msg, oldcmap, queuekey):
        log.debug(score_msg)
        score_msg = self._parse_score_msg(score_msg)
        if not score_msg.valid:
            oldcmap.set(self.answer_id,
                msg = 'Invalid grader reply. Please contact the course staff.')
            return oldcmap

        correctness = 'correct' if score_msg.correct else 'incorrect'

        # TODO: Find out how this is used elsewhere, if any
        self.context['correct'] = correctness

        # Replace 'oldcmap' with new grading results if queuekey matches.  If queuekey
        # does not match, we keep waiting for the score_msg whose key actually matches
        if oldcmap.is_right_queuekey(self.answer_id, queuekey):
            # Sanity check on returned points
            points = score_msg.points
            if points < 0:
                points = 0

            # Queuestate is consumed, so reset it to None
            oldcmap.set(self.answer_id, npoints=points, correctness=correctness,
                msg = score_msg.msg.replace('&nbsp;', '&#160;'), queuestate=None)
        else:
            log.debug('OpenEndedResponse: queuekey {0} does not match for answer_id={1}.'.format(
                queuekey, self.answer_id))

        return oldcmap


    def get_answers(self):
        anshtml = '<span class="openended-answer"><pre><code>{0}</code></pre></span>'.format(self.answer)
        return {self.answer_id: anshtml}

    def get_initial_display(self):
        return {self.answer_id: self.initial_display}

    def _convert_longform_feedback_to_html(self, response_items):
        """
        Take in a dictionary, and return html strings for display to student.
        Input:
            response_items: Dictionary with keys success, feedback.
                if success is True, feedback should be a dictionary, with keys for
                   types of feedback, and the corresponding feedback values.
                if success is False, feedback is actually an error string.

                NOTE: this will need to change when we integrate peer grading, because
                that will have more complex feedback.

        Output:
            String -- html that can be displayed to the student.
        """

        # We want to display available feedback in a particular order.
        # This dictionary specifies which goes first--lower first.
        priorities = {# These go at the start of the feedback
                      'spelling': 0,
                      'grammar': 1,
                      # needs to be after all the other feedback
                      'markup_text': 3}

        default_priority = 2

        def get_priority(elt):
            """
            Args:
                elt: a tuple of feedback-type, feedback
            Returns:
                the priority for this feedback type
            """
            return priorities.get(elt[0], default_priority)

        def encode_values(feedback_type,value):
            feedback_type=str(feedback_type).encode('ascii', 'ignore')
            if not isinstance(value,basestring):
                value=str(value)
            value=value.encode('ascii', 'ignore')
            return feedback_type,value

        def format_feedback(feedback_type, value):
            feedback_type,value=encode_values(feedback_type,value)
            feedback= """
            <div class="{feedback_type}">
            {value}
            </div>
            """.format(feedback_type=feedback_type, value=value)
            return feedback

        def format_feedback_hidden(feedback_type , value):
            feedback_type,value=encode_values(feedback_type,value)
            feedback = """
            <div class="{feedback_type}" style="display: none;">
            {value}
            </div>
            """.format(feedback_type=feedback_type, value=value)
            return feedback

        # TODO (vshnayder): design and document the details of this format so
        # that we can do proper escaping here (e.g. are the graders allowed to
        # include HTML?)

        for tag in ['success', 'feedback', 'submission_id', 'grader_id']:
            if tag not in response_items:
                return format_feedback('errors', 'Error getting feedback')

        feedback_items = response_items['feedback']
        try:
            feedback = json.loads(feedback_items)
        except (TypeError, ValueError):
            log.exception("feedback_items have invalid json %r", feedback_items)
            return format_feedback('errors', 'Could not parse feedback')

        if response_items['success']:
            if len(feedback) == 0:
                return format_feedback('errors', 'No feedback available')

            feedback_lst = sorted(feedback.items(), key=get_priority)
            feedback_list_part1 = u"\n".join(format_feedback(k, v) for k, v in feedback_lst)
        else:
            feedback_list_part1 = format_feedback('errors', response_items['feedback'])

        feedback_list_part2=(u"\n".join([format_feedback_hidden(feedback_type,value)
                                         for feedback_type,value in response_items.items()
                                         if feedback_type in ['submission_id', 'grader_id']]))

        return u"\n".join([feedback_list_part1,feedback_list_part2])

    def _format_feedback(self, response_items):
        """
        Input:
            Dictionary called feedback.  Must contain keys seen below.
        Output:
            Return error message or feedback template
        """

        feedback = self._convert_longform_feedback_to_html(response_items)

        if not response_items['success']:
            return self.system.render_template("open_ended_error.html",
                {'errors' : feedback})

        feedback_template = self.system.render_template("open_ended_feedback.html", {
            'grader_type': response_items['grader_type'],
            'score': "{0} / {1}".format(response_items['score'], self.max_score),
            'feedback': feedback,
            })

        return feedback_template


    def _parse_score_msg(self, score_msg):
        """
         Grader reply is a JSON-dump of the following dict
           { 'correct': True/False,
             'score': Numeric value (floating point is okay) to assign to answer
             'msg': grader_msg
             'feedback' : feedback from grader
             }

        Returns (valid_score_msg, correct, score, msg):
            valid_score_msg: Flag indicating valid score_msg format (Boolean)
            correct:         Correctness of submission (Boolean)
            score:           Points to be assigned (numeric, can be float)
        """
        fail = ScoreMessage(valid=False, correct=False, points=0, msg='')
        try:
            score_result = json.loads(score_msg)
        except (TypeError, ValueError):
            log.error("External grader message should be a JSON-serialized dict."
                      " Received score_msg = {0}".format(score_msg))
            return fail

        if not isinstance(score_result, dict):
            log.error("External grader message should be a JSON-serialized dict."
                      " Received score_result = {0}".format(score_result))
            return fail

        for tag in ['score', 'feedback', 'grader_type', 'success', 'grader_id', 'submission_id']:
            if tag not in score_result:
                log.error("External grader message is missing required tag: {0}"
                .format(tag))
                return fail

        feedback = self._format_feedback(score_result)
        self.submission_id=score_result['submission_id']
        self.grader_id=score_result['grader_id']

        # HACK: for now, just assume it's correct if you got more than 2/3.
        # Also assumes that score_result['score'] is an integer.
        score_ratio = int(score_result['score']) / float(self.max_score)
        correct = (score_ratio >= 0.66)

        #Currently ignore msg and only return feedback (which takes the place of msg)
        return ScoreMessage(valid=True, correct=correct,
            points=score_result['score'], msg=feedback)

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
            'problem_get': self.get_problem,
            'problem_reset': self.reset_problem,
            'problem_save': self.save_problem,
            'score_update': self.update_score,
            'message_post' : self.message_post,
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

    def get_problem(self, get):
        return self.get_html()

    def reset_problem(self, get):
        self.change_state(self.INITIAL)
        return {'success': True}

    def save_problem(self, get):
        pass

    def update_score(self, get):
        """
        Delivers grading response (e.g. from asynchronous code checking) to
            the capa problem, so its score can be updated

        'get' must have a field 'response' which is a string that contains the
            grader's response

        No ajax return is needed. Return empty dict.
        """
        queuekey = get['queuekey']
        score_msg = get['xqueue_body']
        #TODO: Remove need for cmap
        self._update_score(score_msg, queuekey)

        return dict()  # No AJAX return is needed

    def get_html(self):
        """
        Implement special logic: handle queueing state, and default input.
        """
        # if no student input yet, then use the default input given by the problem
        if not self.value:
            self.value = self.xml.text

        # Check if problem has been queued
        self.queue_len = 0
        # Flag indicating that the problem has been queued, 'msg' is length of queue
        if self.status == 'incomplete':
            self.status = 'queued'
            self.queue_len = self.msg
            self.msg = self.submitted_msg

        context={'rows' : 30,
                 'cols' : 80,
                 'hidden' : '',
                 'id' : 'open_ended',
                 'msg' : self.msg,
                 'status' : self.status,
                 'queue_len' : self.queue_len,
                 'value' : self.value,
                 }

        html=self.system.render_template("open_ended.html", context)
        return html

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


class OpenEndedDescriptor(XmlDescriptor, EditingDescriptor):
    """
    Module for adding self assessment questions to courses
    """
    mako_template = "widgets/html-edit.html"
    module_class = OpenEndedModule
    filename_extension = "xml"

    stores_state = True
    has_score = True
    template_dir_name = "openended"

    js = {'coffee': [resource_string(__name__, 'js/src/html/edit.coffee')]}
    js_module_name = "HTMLEditingDescriptor"
    expected_children = ['rubric', 'prompt', 'oeparam']

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

        for child in self.expected_children:
            if len(xml_object.xpath(child)) != 1:
                raise ValueError("Open Ended definition must include exactly one '{0}' tag".format(child))

        def parse(k):
            """Assumes that xml_object has child k"""
            return stringify_children(xml_object.xpath(k)[0])

        return {'rubric': parse('rubric'),
                'prompt': parse('prompt'),
                'oeparam': parse('oeparam'),
                }


    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        elt = etree.Element('openended')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in self.expected_children:
            add_child(child)

        return elt


