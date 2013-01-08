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
from .xml_module import XmlDescriptor
from xmodule.modulestore import Location
from capa.util import *
import openendedchild

from mitxmako.shortcuts import render_to_string

from datetime import datetime

log = logging.getLogger("mitx.courseware")

class OpenEndedModule(openendedchild.OpenEndedChild):

    def setup_response(self, system, location, definition, descriptor):
        oeparam = definition['oeparam']
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

        self._parse(oeparam, prompt, rubric, system)

        if self.created=="True" and self.state == self.ASSESSING:
            self.created="False"
            self.send_to_grader(self.latest_answer(), system)
            self.created="False"

    def _parse(self, oeparam, prompt, rubric, system):
        '''
        Parse OpenEndedResponse XML:
            self.initial_display
            self.payload - dict containing keys --
            'grader' : path to grader settings file, 'problem_id' : id of the problem

            self.answer - What to display when show answer is clicked
        '''
        # Note that OpenEndedResponse is agnostic to the specific contents of grader_payload
        prompt_string = stringify_children(prompt)
        rubric_string = stringify_children(rubric)
        self.prompt=prompt_string

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
            'location' : system.location.url(),
            'course_id' : system.course_id,
            'prompt' : prompt_string,
            'rubric' : rubric_string,
            'initial_display' : self.initial_display,
            'answer' : self.answer,
            })
        updated_grader_payload = json.dumps(parsed_grader_payload)

        self.payload = {'grader_payload': updated_grader_payload}

    def skip_post_assessment(self, get, system):
        self.state=self.DONE
        return {'success' : True}

    def message_post(self,get, system):
        """
        Handles a student message post (a reaction to the grade they received from an open ended grader type)
        Returns a boolean success/fail and an error message
        """

        event_info = dict()
        event_info['problem_id'] = system.location.url()
        event_info['student_id'] = system.anonymous_student_id
        event_info['survey_responses']= get

        survey_responses=event_info['survey_responses']
        for tag in ['feedback', 'submission_id', 'grader_id', 'score']:
            if tag not in survey_responses:
                return {'success' : False, 'msg' : "Could not find needed tag {0}".format(tag)}
        try:
            submission_id=int(survey_responses['submission_id'])
            grader_id = int(survey_responses['grader_id'])
            feedback = str(survey_responses['feedback'].encode('ascii', 'ignore'))
            score = int(survey_responses['score'])
        except:
            error_message=("Could not parse submission id, grader id, "
                           "or feedback from message_post ajax call.  Here is the message data: {0}".format(survey_responses))
            log.exception(error_message)
            return {'success' : False, 'msg' : "There was an error saving your feedback.  Please contact course staff."}

        qinterface = system.xqueue['interface']
        qtime = datetime.strftime(datetime.now(), xqueue_interface.dateformat)
        anonymous_student_id = system.anonymous_student_id
        queuekey = xqueue_interface.make_hashkey(str(system.seed) + qtime +
                                                 anonymous_student_id +
                                                 str(len(self.history)))

        xheader = xqueue_interface.make_xheader(
            lms_callback_url=system.xqueue['callback_url'],
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

        self.state=self.DONE

        return {'success' : success, 'msg' : "Successfully submitted your feedback."}

    def send_to_grader(self, submission, system):

        # Prepare xqueue request
        #------------------------------------------------------------

        qinterface = system.xqueue['interface']
        qtime = datetime.strftime(datetime.now(), xqueue_interface.dateformat)

        anonymous_student_id = system.anonymous_student_id

        # Generate header
        queuekey = xqueue_interface.make_hashkey(str(system.seed) + qtime +
                                                 anonymous_student_id +
                                                 str(len(self.history)))

        xheader = xqueue_interface.make_xheader(lms_callback_url=system.xqueue['callback_url'],
            lms_key=queuekey,
            queue_name=self.queue_name)

        contents = self.payload.copy()

        # Metadata related to the student submission revealed to the external grader
        student_info = {'anonymous_student_id': anonymous_student_id,
                        'submission_time': qtime,
                        }

        #Update contents with student response and student info
        contents.update({
            'student_info': json.dumps(student_info),
            'student_response': submission,
            'max_score' : self.max_score(),
            })

        # Submit request. When successful, 'msg' is the prior length of the queue
        (error, msg) = qinterface.send_to_queue(header=xheader,
            body=json.dumps(contents))

        # State associated with the queueing request
        queuestate = {'key': queuekey,
                      'time': qtime,}
        return True

    def _update_score(self, score_msg, queuekey, system):
        new_score_msg = self._parse_score_msg(score_msg)
        if not new_score_msg['valid']:
            score_msg['feedback'] = 'Invalid grader reply. Please contact the course staff.'

        self.record_latest_score(new_score_msg['score'])
        self.record_latest_post_assessment(score_msg)
        self.state=self.POST_ASSESSMENT

        return True


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
            return system.render_template("open_ended_error.html",
                {'errors' : feedback})

        feedback_template = render_to_string("open_ended_feedback.html", {
            'grader_type': response_items['grader_type'],
            'score': "{0} / {1}".format(response_items['score'], self.max_score()),
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
        fail = {'valid' : False, 'correct' : False, 'points' : 0, 'msg' : ''}
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

        return {'valid' : True, 'score' : score_result['score'], 'feedback' : feedback}

    def latest_post_assessment(self, short_feedback=False):
        """None if not available"""
        if not self.history:
            return ""

        feedback_dict = self._parse_score_msg(self.history[-1].get('post_assessment', ""))
        if not short_feedback:
            return feedback_dict['feedback'] if feedback_dict['valid'] else ''
        if feedback_dict['valid']:
            short_feedback = self._convert_longform_feedback_to_html(json.loads(self.history[-1].get('post_assessment', "")))
        return short_feedback if feedback_dict['valid'] else ''

    def is_submission_correct(self, score):
        correct=False
        if(isinstance(score,(int, long, float, complex))):
            score_ratio = int(score) / float(self.max_score())
            correct = (score_ratio >= 0.66)
        return correct

    def format_feedback_with_evaluation(self,feedback):
        context={'msg' : feedback, 'id' : "1", 'rows' : 50, 'cols' : 50}
        html= render_to_string('open_ended_evaluation.html', context)
        return html

    def handle_ajax(self, dispatch, get, system):
        '''
        This is called by courseware.module_render, to handle an AJAX call.
        "get" is request.POST.

        Returns a json dictionary:
        { 'progress_changed' : True/False,
          'progress' : 'none'/'in_progress'/'done',
          <other request-specific values here > }
        '''
        handlers = {
            'save_answer': self.save_answer,
            'score_update': self.update_score,
            'save_post_assessment' : self.message_post,
            'skip_post_assessment' : self.skip_post_assessment,
            'check_for_score' : self.check_for_score,
            }

        if dispatch not in handlers:
            return 'Error'

        before = self.get_progress()
        d = handlers[dispatch](get, system)
        after = self.get_progress()
        d.update({
            'progress_changed': after != before,
            'progress_status': Progress.to_js_status_str(after),
            })
        return json.dumps(d, cls=ComplexEncoder)

    def check_for_score(self, get, system):
        state = self.state
        return {'state' : state}

    def save_answer(self, get, system):
        if self.attempts > self.max_attempts:
            # If too many attempts, prevent student from saving answer and
            # seeing rubric.  In normal use, students shouldn't see this because
            # they won't see the reset button once they're out of attempts.
            return {
                'success': False,
                'error': 'Too many attempts.'
            }

        if self.state != self.INITIAL:
            return self.out_of_sync_error(get)

        # add new history element with answer and empty score and hint.
        self.new_history_entry(get['student_answer'])
        self.send_to_grader(get['student_answer'], system)
        self.change_state(self.ASSESSING)

        return {'success': True,}

    def update_score(self, get, system):
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
        self._update_score(score_msg, queuekey, system)

        return dict()  # No AJAX return is needed

    def get_html(self, system):
        #set context variables and render template
        if self.state != self.INITIAL:
            latest = self.latest_answer()
            previous_answer = latest if latest is not None else self.initial_display
            post_assessment = self.latest_post_assessment()
            score= self.latest_score()
            correct = 'correct' if self.is_submission_correct(score) else 'incorrect'
        else:
            post_assessment=""
            correct=""
            previous_answer = self.initial_display

        context = {
            'prompt': self.prompt,
            'previous_answer': previous_answer,
            'state': self.state,
            'allow_reset': self._allow_reset(),
            'rows' : 30,
            'cols' : 80,
            'id' : 'open_ended',
            'msg' : post_assessment,
            'child_type' : 'openended',
            'correct' : correct,
            }
        log.debug(context)
        html = system.render_template('open_ended.html', context)
        return html

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

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Pull out the rubric, prompt, and submitmessage into a dictionary.

        Returns:
        {
        'rubric': 'some-html',
        'prompt': 'some-html',
        'oeparam': 'some-html'
        }
        """

        for child in ['openendedrubric', 'prompt', 'openendedparam']:
            if len(xml_object.xpath(child)) != 1:
                raise ValueError("Open Ended definition must include exactly one '{0}' tag".format(child))

        def parse(k):
            """Assumes that xml_object has child k"""
            return xml_object.xpath(k)[0]

        return {'rubric': parse('openendedrubric'),
                'prompt': parse('prompt'),
                'oeparam': parse('openendedparam'),
                }


    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        elt = etree.Element('openended')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in ['openendedrubric', 'prompt', 'openendedparam']:
            add_child(child)

        return elt


