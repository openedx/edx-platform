"""
A Self Assessment module that allows students to write open-ended responses,
submit, then see a rubric and rate themselves.  Persists student supplied
hints, answers, and assessment judgment (currently only correct/incorrect).
Parses xml definition file--see below for exact format.
"""

import json
import logging
from lxml import etree
import capa.xqueue_interface as xqueue_interface

from xmodule.capa_module import ComplexEncoder
from xmodule.progress import Progress
from xmodule.stringify import stringify_children
from capa.util import *
import openendedchild

from numpy import median

from datetime import datetime
from pytz import UTC

from .combined_open_ended_rubric import CombinedOpenEndedRubric

log = logging.getLogger("edx.courseware")


class OpenEndedModule(openendedchild.OpenEndedChild):
    """
    The open ended module supports all external open ended grader problems.
    Sample XML file:
    <openended min_score_to_attempt="1" max_score_to_attempt="1">
        <openendedparam>
            <initial_display>Enter essay here.</initial_display>
            <answer_display>This is the answer.</answer_display>
            <grader_payload>{"grader_settings" : "ml_grading.conf", "problem_id" : "6.002x/Welcome/OETest"}</grader_payload>
        </openendedparam>
    </openended>
    """

    TEMPLATE_DIR = "combinedopenended/openended"

    def setup_response(self, system, location, definition, descriptor):
        """
        Sets up the response type.
        @param system: Modulesystem object
        @param location: The location of the problem
        @param definition: The xml definition of the problem
        @param descriptor: The OpenEndedDescriptor associated with this
        @return: None
        """
        oeparam = definition['oeparam']

        self.url = definition.get('url', None)
        self.queue_name = definition.get('queuename', self.DEFAULT_QUEUE)
        self.message_queue_name = definition.get('message-queuename', self.DEFAULT_MESSAGE_QUEUE)

        # This is needed to attach feedback to specific responses later
        self.submission_id = None
        self.grader_id = None

        error_message = "No {0} found in problem xml for open ended problem. Contact the learning sciences group for assistance."
        if oeparam is None:
            # This is a staff_facing_error
            raise ValueError(error_message.format('oeparam'))
        if self.child_prompt is None:
            raise ValueError(error_message.format('prompt'))
        if self.child_rubric is None:
            raise ValueError(error_message.format('rubric'))

        self._parse(oeparam, self.child_prompt, self.child_rubric, system)

        # If there are multiple tasks (like self-assessment followed by ai), once
        # the the status of the first task is set to DONE, setup_next_task() will
        # create the OpenEndedChild with parameter child_created=True so that the
        # submission can be sent to the grader. Keep trying each time this module
        # is loaded until it succeeds.
        if self.child_created is True and self.child_state == self.ASSESSING:
            success, message = self.send_to_grader(self.latest_answer(), system)
            if success:
                self.child_created = False

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
        self.child_prompt = prompt_string
        self.child_rubric = rubric_string

        grader_payload = oeparam.find('grader_payload')
        grader_payload = grader_payload.text if grader_payload is not None else ''

        # Update grader payload with student id.  If grader payload not json, error.
        try:
            parsed_grader_payload = json.loads(grader_payload)
            # NOTE: self.system.location is valid because the capa_module
            # __init__ adds it (easiest way to get problem location into
            # response types)
        except (TypeError, ValueError):
            # This is a dev_facing_error
            log.exception(
                "Grader payload from external open ended grading server is not a json object! Object: {0}".format(
                    grader_payload))

        self.initial_display = find_with_default(oeparam, 'initial_display', '')
        self.answer = find_with_default(oeparam, 'answer_display', 'No answer given.')

        parsed_grader_payload.update({
            'location': self.location_string,
            'course_id': system.course_id.to_deprecated_string(),
            'prompt': prompt_string,
            'rubric': rubric_string,
            'initial_display': self.initial_display,
            'answer': self.answer,
            'problem_id': self.display_name,
            'skip_basic_checks': self.skip_basic_checks,
            'control': json.dumps(self.control),
        })
        updated_grader_payload = json.dumps(parsed_grader_payload)

        self.payload = {'grader_payload': updated_grader_payload}

    def skip_post_assessment(self, _data, system):
        """
        Ajax function that allows one to skip the post assessment phase
        @param data: AJAX dictionary
        @param system: ModuleSystem
        @return: Success indicator
        """
        self.child_state = self.DONE
        return {'success': True}

    def message_post(self, data, system):
        """
        Handles a student message post (a reaction to the grade they received from an open ended grader type)
        Returns a boolean success/fail and an error message
        """

        event_info = dict()
        event_info['problem_id'] = self.location_string
        event_info['student_id'] = system.anonymous_student_id
        event_info['survey_responses'] = data
        _ = self.system.service(self, "i18n").ugettext

        survey_responses = event_info['survey_responses']
        for tag in ['feedback', 'submission_id', 'grader_id', 'score']:
            if tag not in survey_responses:
                # This is a student_facing_error
                return {
                    'success': False,
                    # Translators: 'tag' is one of 'feedback', 'submission_id',
                    # 'grader_id', or 'score'. They are categories that a student
                    # responds to when filling out a post-assessment survey
                    # of his or her grade from an openended problem.
                    'msg': _("Could not find needed tag {tag_name} in the "
                             "survey responses. Please try submitting "
                             "again.").format(tag_name=tag)
                }
        try:
            submission_id = int(survey_responses['submission_id'])
            grader_id = int(survey_responses['grader_id'])
            feedback = str(survey_responses['feedback'].encode('ascii', 'ignore'))
            score = int(survey_responses['score'])
        except:
            # This is a dev_facing_error
            error_message = (
                "Could not parse submission id, grader id, "
                "or feedback from message_post ajax call.  "
                "Here is the message data: {0}".format(survey_responses)
            )
            log.exception(error_message)
            # This is a student_facing_error
            return {
                'success': False,
                'msg': _(
                    "There was an error saving your feedback. Please "
                    "contact course staff."
                )
            }

        xqueue = system.get('xqueue')
        if xqueue is None:
            return {'success': False, 'msg': _("Couldn't submit feedback.")}
        qinterface = xqueue['interface']
        qtime = datetime.strftime(datetime.now(UTC), xqueue_interface.dateformat)
        anonymous_student_id = system.anonymous_student_id
        queuekey = xqueue_interface.make_hashkey(str(system.seed) + qtime +
                                                 anonymous_student_id +
                                                 str(len(self.child_history)))

        xheader = xqueue_interface.make_xheader(
            lms_callback_url=xqueue['construct_callback'](),
            lms_key=queuekey,
            queue_name=self.message_queue_name
        )

        student_info = {
            'anonymous_student_id': anonymous_student_id,
            'submission_time': qtime,
        }
        contents = {
            'feedback': feedback,
            'submission_id': submission_id,
            'grader_id': grader_id,
            'score': score,
            'student_info': json.dumps(student_info),
        }

        error, error_message = qinterface.send_to_queue(
            header=xheader,
            body=json.dumps(contents)
        )

        # Convert error to a success value
        success = True
        message = _("Successfully saved your feedback.")
        if error:
            success = False
            message = _("Unable to save your feedback. Please try again later.")
            log.error("Unable to send feedback to grader. location: {0}, error_message: {1}".format(
                self.location_string, error_message
            ))
        else:
            self.child_state = self.DONE

        # This is a student_facing_message
        return {'success': success, 'msg': message}

    def send_to_grader(self, submission, system):
        """
        Send a given submission to the grader, via the xqueue
        @param submission: The student submission to send to the grader
        @param system: Modulesystem
        @return: Boolean true (not useful right now)
        """

        # Prepare xqueue request
        #------------------------------------------------------------

        xqueue = system.get('xqueue')
        if xqueue is None:
            return False
        qinterface = xqueue['interface']
        qtime = datetime.strftime(datetime.now(UTC), xqueue_interface.dateformat)

        anonymous_student_id = system.anonymous_student_id

        # Generate header
        queuekey = xqueue_interface.make_hashkey(str(system.seed) + qtime +
                                                 anonymous_student_id +
                                                 str(len(self.child_history)))

        xheader = xqueue_interface.make_xheader(
            lms_callback_url=xqueue['construct_callback'](),
            lms_key=queuekey,
            queue_name=self.queue_name
        )

        contents = self.payload.copy()

        # Metadata related to the student submission revealed to the external grader
        student_info = {
            'anonymous_student_id': anonymous_student_id,
            'submission_time': qtime,
        }

        # Update contents with student response and student info
        contents.update({
            'student_info': json.dumps(student_info),
            'student_response': submission,
            'max_score': self.max_score(),
        })

        # Submit request. When successful, 'msg' is the prior length of the queue
        error, error_message = qinterface.send_to_queue(
            header=xheader,
            body=json.dumps(contents)
        )

        # State associated with the queueing request
        queuestate = {
            'key': queuekey,
            'time': qtime,
        }
        _ = self.system.service(self, "i18n").ugettext
        success = True
        message = _("Successfully saved your submission.")
        if error:
            success = False
            # Translators: the `grader` refers to the grading service open response problems
            # are sent to, either to be machine-graded, peer-graded, or instructor-graded.
            message = _('Unable to submit your submission to the grader. Please try again later.')
            log.error("Unable to submit to grader. location: {0}, error_message: {1}".format(
                self.location_string, error_message
            ))

        return (success, message)

    def _update_score(self, score_msg, queuekey, system):
        """
        Called by xqueue to update the score
        @param score_msg: The message from xqueue
        @param queuekey: The key sent by xqueue
        @param system: Modulesystem
        @return: Boolean True (not useful currently)
        """
        _ = self.system.service(self, "i18n").ugettext
        new_score_msg = self._parse_score_msg(score_msg, system)
        if not new_score_msg['valid']:
            # Translators: the `grader` refers to the grading service open response problems
            # are sent to, either to be machine-graded, peer-graded, or instructor-graded.
            new_score_msg['feedback'] = _('Invalid grader reply. Please contact the course staff.')

        # self.child_history is initialized as [].  record_latest_score() and record_latest_post_assessment()
        # operate on self.child_history[-1].  Thus we have to make sure child_history is not [].
        # Handle at this level instead of in record_*() because this is a good place to reduce the number of conditions
        # and also keep the persistent state from changing.
        if self.child_history:
            self.record_latest_score(new_score_msg['score'])
            self.record_latest_post_assessment(score_msg)
            self.child_state = self.POST_ASSESSMENT
        else:
            log.error(
                "Trying to update score without existing studentmodule child_history:\n"
                "   location: {location}\n"
                "   score: {score}\n"
                "   grader_ids: {grader_ids}\n"
                "   submission_ids: {submission_ids}".format(
                    location=self.location_string,
                    score=new_score_msg['score'],
                    grader_ids=new_score_msg['grader_ids'],
                    submission_ids=new_score_msg['submission_ids'],
                )
            )

        return True

    def get_answers(self):
        """
        Gets and shows the answer for this problem.
        @return: Answer html
        """
        anshtml = '<span class="openended-answer"><pre><code>{0}</code></pre></span>'.format(self.answer)
        return {self.answer_id: anshtml}

    def get_initial_display(self):
        """
        Gets and shows the initial display for the input box.
        @return: Initial display html
        """
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
            String -- html that can be displayincorrect-icon.pnged to the student.
        """

        # We want to display available feedback in a particular order.
        # This dictionary specifies which goes first--lower first.
        priorities = {
            # These go at the start of the feedback
            'spelling': 0,
            'grammar': 1,
            # needs to be after all the other feedback
            'markup_text': 3
        }
        do_not_render = ['topicality', 'prompt-overlap']

        default_priority = 2

        def get_priority(elt):
            """
            Args:
                elt: a tuple of feedback-type, feedback
            Returns:
                the priority for this feedback type
            """
            return priorities.get(elt[0], default_priority)

        def encode_values(feedback_type, value):
            feedback_type = str(feedback_type).encode('ascii', 'ignore')
            if not isinstance(value, basestring):
                value = str(value)
            value = value.encode('ascii', 'ignore')
            return feedback_type, value

        def format_feedback(feedback_type, value):
            feedback_type, value = encode_values(feedback_type, value)
            feedback = u"""
            <div class="{feedback_type}">
            {value}
            </div>
            """.format(feedback_type=feedback_type, value=value)
            return feedback

        def format_feedback_hidden(feedback_type, value):
            feedback_type, value = encode_values(feedback_type, value)
            feedback = """
            <input class="{feedback_type}" type="hidden" value="{value}" />
            """.format(feedback_type=feedback_type, value=value)
            return feedback

        # TODO (vshnayder): design and document the details of this format so
        # that we can do proper escaping here (e.g. are the graders allowed to
        # include HTML?)

        _ = self.system.service(self, "i18n").ugettext
        for tag in ['success', 'feedback', 'submission_id', 'grader_id']:
            if tag not in response_items:
                # This is a student_facing_error
                return format_feedback(
                    # Translators: the `grader` refers to the grading service open response problems
                    # are sent to, either to be machine-graded, peer-graded, or instructor-graded.
                    'errors', _('Error getting feedback from grader.')
                )

        feedback_items = response_items['feedback']
        try:
            feedback = json.loads(feedback_items)
        except (TypeError, ValueError):
            # This is a dev_facing_error
            log.exception("feedback_items from external open ended grader have invalid json {0}".format(feedback_items))
            # This is a student_facing_error
            return format_feedback(
                # Translators: the `grader` refers to the grading service open response problems
                # are sent to, either to be machine-graded, peer-graded, or instructor-graded.
                'errors', _('Error getting feedback from grader.')
            )

        if response_items['success']:
            if len(feedback) == 0:
                # This is a student_facing_error
                return format_feedback(
                    # Translators: the `grader` refers to the grading service open response problems
                    # are sent to, either to be machine-graded, peer-graded, or instructor-graded.
                    'errors', _('No feedback available from grader.')
                )

            for tag in do_not_render:
                if tag in feedback:
                    feedback.pop(tag)

            feedback_lst = sorted(feedback.items(), key=get_priority)
            feedback_list_part1 = u"\n".join(format_feedback(k, v) for k, v in feedback_lst)
        else:
            # This is a student_facing_error
            feedback_list_part1 = format_feedback('errors', response_items['feedback'])

        feedback_list_part2 = (u"\n".join([format_feedback_hidden(feedback_type, value)
                                           for feedback_type, value in response_items.items()
                                           if feedback_type in ['submission_id', 'grader_id']]))

        return u"\n".join([feedback_list_part1, feedback_list_part2])

    def _format_feedback(self, response_items, system):
        """
        Input:
            Dictionary called feedback.  Must contain keys seen below.
        Output:
            Return error message or feedback template
        """

        rubric_feedback = ""
        feedback = self._convert_longform_feedback_to_html(response_items)
        rubric_scores = []
        if response_items['rubric_scores_complete'] is True:
            rubric_renderer = CombinedOpenEndedRubric(system.render_template, True)
            rubric_dict = rubric_renderer.render_rubric(response_items['rubric_xml'])
            success = rubric_dict['success']
            rubric_feedback = rubric_dict['html']
            rubric_scores = rubric_dict['rubric_scores']

        if not response_items['success']:
            return system.render_template(
                "{0}/open_ended_error.html".format(self.TEMPLATE_DIR),
                {'errors': feedback}
            )

        feedback_template = system.render_template("{0}/open_ended_feedback.html".format(self.TEMPLATE_DIR), {
            'grader_type': response_items['grader_type'],
            'score': "{0} / {1}".format(response_items['score'], self.max_score()),
            'feedback': feedback,
            'rubric_feedback': rubric_feedback
        })

        return feedback_template, rubric_scores

    def _parse_score_msg(self, score_msg, system, join_feedback=True):
        """
         Grader reply is a JSON-dump of the following dict
           { 'correct': True/False,
             'score': Numeric value (floating point is okay) to assign to answer
             'msg': grader_msg
             'feedback' : feedback from grader
             'grader_type': what type of grader resulted in this score
             'grader_id': id of the grader
             'submission_id' : id of the submission
             'success': whether or not this submission was successful
             'rubric_scores': a list of rubric scores
             'rubric_scores_complete': boolean if rubric scores are complete
             'rubric_xml': the xml of the rubric in string format
             }

        Returns (valid_score_msg, correct, score, msg):
            valid_score_msg: Flag indicating valid score_msg format (Boolean)
            correct:         Correctness of submission (Boolean)
            score:           Points to be assigned (numeric, can be float)
        """
        fail = {
            'valid': False,
            'score': 0,
            'feedback': '',
            'rubric_scores': [[0]],
            'grader_types': [''],
            'feedback_items': [''],
            'feedback_dicts': [{}],
            'grader_ids': [0],
            'submission_ids': [0],
        }
        try:
            score_result = json.loads(score_msg)
        except (TypeError, ValueError):
            # This is a dev_facing_error
            error_message = ("External open ended grader message should be a JSON-serialized dict."
                             " Received score_msg = {0}".format(score_msg))
            log.error(error_message)
            fail['feedback'] = error_message
            return fail

        if not isinstance(score_result, dict):
            # This is a dev_facing_error
            error_message = ("External open ended grader message should be a JSON-serialized dict."
                             " Received score_result = {0}".format(score_result))
            log.error(error_message)
            fail['feedback'] = error_message
            return fail

        if not score_result:
            return fail

        for tag in ['score', 'feedback', 'grader_type', 'success', 'grader_id', 'submission_id']:
            if tag not in score_result:
                # This is a dev_facing_error
                error_message = ("External open ended grader message is missing required tag: {0}"
                                 .format(tag))
                log.error(error_message)
                fail['feedback'] = error_message
                return fail
                # This is to support peer grading
        if isinstance(score_result['score'], list):
            feedback_items = []
            rubric_scores = []
            grader_types = []
            feedback_dicts = []
            grader_ids = []
            submission_ids = []
            for i in xrange(len(score_result['score'])):
                new_score_result = {
                    'score': score_result['score'][i],
                    'feedback': score_result['feedback'][i],
                    'grader_type': score_result['grader_type'],
                    'success': score_result['success'],
                    'grader_id': score_result['grader_id'][i],
                    'submission_id': score_result['submission_id'],
                    'rubric_scores_complete': score_result['rubric_scores_complete'][i],
                    'rubric_xml': score_result['rubric_xml'][i],
                }
                feedback_template, rubric_score = self._format_feedback(new_score_result, system)
                feedback_items.append(feedback_template)
                rubric_scores.append(rubric_score)
                grader_types.append(score_result['grader_type'])
                try:
                    feedback_dict = json.loads(score_result['feedback'][i])
                except Exception:
                    feedback_dict = score_result['feedback'][i]
                feedback_dicts.append(feedback_dict)
                grader_ids.append(score_result['grader_id'][i])
                submission_ids.append(score_result['submission_id'])
            if join_feedback:
                feedback = "".join(feedback_items)
            else:
                feedback = feedback_items
            score = int(round(median(score_result['score'])))
        else:
            # This is for instructor and ML grading
            feedback, rubric_score = self._format_feedback(score_result, system)
            score = score_result['score']
            rubric_scores = [rubric_score]
            grader_types = [score_result['grader_type']]
            feedback_items = [feedback]
            try:
                feedback_dict = json.loads(score_result['feedback'])
            except Exception:
                feedback_dict = score_result.get('feedback', '')
            feedback_dicts = [feedback_dict]
            grader_ids = [score_result['grader_id']]
            submission_ids = [score_result['submission_id']]

        self.submission_id = score_result['submission_id']
        self.grader_id = score_result['grader_id']

        return {
            'valid': True,
            'score': score,
            'feedback': feedback,
            'rubric_scores': rubric_scores,
            'grader_types': grader_types,
            'feedback_items': feedback_items,
            'feedback_dicts': feedback_dicts,
            'grader_ids': grader_ids,
            'submission_ids': submission_ids,
        }

    def latest_post_assessment(self, system, short_feedback=False, join_feedback=True):
        """
        Gets the latest feedback, parses, and returns
        @param short_feedback: If the long feedback is wanted or not
        @return: Returns formatted feedback
        """
        if not self.child_history:
            return ""

        feedback_dict = self._parse_score_msg(
            self.child_history[-1].get('post_assessment', "{}"),
            system,
            join_feedback=join_feedback
        )
        if not short_feedback:
            return feedback_dict['feedback'] if feedback_dict['valid'] else ''
        if feedback_dict['valid']:
            short_feedback = self._convert_longform_feedback_to_html(
                json.loads(self.child_history[-1].get('post_assessment', "")))
        return short_feedback if feedback_dict['valid'] else ''

    def format_feedback_with_evaluation(self, system, feedback):
        """
        Renders a given html feedback into an evaluation template
        @param feedback: HTML feedback
        @return: Rendered html
        """
        context = {'msg': feedback, 'id': "1", 'rows': 50, 'cols': 50}
        html = system.render_template('{0}/open_ended_evaluation.html'.format(self.TEMPLATE_DIR), context)
        return html

    def handle_ajax(self, dispatch, data, system):
        '''
        This is called by courseware.module_render, to handle an AJAX call.
        "data" is request.POST.

        Returns a json dictionary:
        { 'progress_changed' : True/False,
          'progress' : 'none'/'in_progress'/'done',
          <other request-specific values here > }
        '''
        handlers = {
            'save_answer': self.save_answer,
            'score_update': self.update_score,
            'save_post_assessment': self.message_post,
            'skip_post_assessment': self.skip_post_assessment,
            'check_for_score': self.check_for_score,
            'store_answer': self.store_answer,
        }
        _ = self.system.service(self, "i18n").ugettext
        if dispatch not in handlers:
            # This is a dev_facing_error
            log.error("Cannot find {0} in handlers in handle_ajax function for open_ended_module.py".format(dispatch))
            # This is a dev_facing_error
            return json.dumps(
                {'error': _('Error handling action. Please try again.'), 'success': False}
            )

        before = self.get_progress()
        d = handlers[dispatch](data, system)
        after = self.get_progress()
        d.update({
            'progress_changed': after != before,
            'progress_status': Progress.to_js_status_str(after),
        })
        return json.dumps(d, cls=ComplexEncoder)

    def check_for_score(self, _data, system):
        """
        Checks to see if a score has been received yet.
        @param data: AJAX dictionary
        @param system: Modulesystem (needed to align with other ajax functions)
        @return: Returns the current state
        """
        state = self.child_state
        return {'state': state}

    def save_answer(self, data, system):
        """
        Saves a student answer
        @param data: AJAX dictionary
        @param system: modulesystem
        @return: Success indicator
        """
        # Once we close the problem, we should not allow students
        # to save answers
        error_message = ""
        closed, msg = self.check_if_closed()
        if closed:
            return msg

        if self.child_state != self.INITIAL:
            return self.out_of_sync_error(data)

        message = "Successfully saved your submission."

        # add new history element with answer and empty score and hint.
        success, error_message, data = self.append_file_link_to_student_answer(data)
        if not success:
            message = error_message
        else:
            data['student_answer'] = OpenEndedModule.sanitize_html(data['student_answer'])
            success, error_message = self.send_to_grader(data['student_answer'], system)
            if not success:
                message = error_message
                # Store the answer instead
                self.store_answer(data, system)
            else:
                self.new_history_entry(data['student_answer'])
                self.change_state(self.ASSESSING)

        return {
            'success': success,
            'error': message,
            'student_response': data['student_answer'].replace("\n", "<br/>")
        }

    def update_score(self, data, system):
        """
        Updates the current score via ajax.  Called by xqueue.
        Input: AJAX data dictionary, modulesystem
        Output: None
        """
        queuekey = data['queuekey']
        score_msg = data['xqueue_body']
        # TODO: Remove need for cmap
        self._update_score(score_msg, queuekey, system)

        return dict()  # No AJAX return is needed

    def get_html(self, system):
        """
        Gets the HTML for this problem and renders it
        Input: Modulesystem object
        Output: Rendered HTML
        """
        _ = self.system.service(self, "i18n").ugettext
        # set context variables and render template
        eta_string = None
        if self.child_state != self.INITIAL:
            post_assessment = self.latest_post_assessment(system)
            score = self.latest_score()
            correct = 'correct' if self.is_submission_correct(score) else 'incorrect'
            if self.child_state == self.ASSESSING:
                # Translators: this string appears once an openended response
                # is submitted but before it has been graded
                eta_string = _("Your response has been submitted. Please check back later for your grade.")
        else:
            post_assessment = ""
            correct = ""
        previous_answer = self.get_display_answer()

        # Use the module name as a unique id to pass to the template.
        try:
            module_id = self.system.location.name
        except AttributeError:
            # In cases where we don't have a system or a location, use a fallback.
            module_id = "open_ended"

        context = {
            'prompt': self.child_prompt,
            'previous_answer': previous_answer,
            'state': self.child_state,
            'allow_reset': self._allow_reset(),
            'rows': 30,
            'cols': 80,
            'module_id': module_id,
            'msg': post_assessment,
            'child_type': 'openended',
            'correct': correct,
            'accept_file_upload': self.accept_file_upload,
            'eta_message': eta_string,
        }
        html = system.render_template('{0}/open_ended.html'.format(self.TEMPLATE_DIR), context)
        return html

    def latest_score(self):
        """None if not available"""
        if not self.child_history:
            return None
        return self.score_for_attempt(-1)

    def all_scores(self):
        """None if not available"""
        if not self.child_history:
            return None
        return [self.score_for_attempt(index) for index in xrange(len(self.child_history))]

    def score_for_attempt(self, index):
        """
        Return sum of rubric scores for ML grading otherwise return attempt["score"].
        """
        attempt = self.child_history[index]
        score = attempt.get('score')
        post_assessment_data = self._parse_score_msg(attempt.get('post_assessment', "{}"), self.system)
        grader_types = post_assessment_data.get('grader_types')

        # According to _parse_score_msg in ML grading there should be only one grader type.
        if len(grader_types) == 1 and grader_types[0] == 'ML':
            rubric_scores = post_assessment_data.get("rubric_scores")

            # Similarly there should be only one list of rubric scores.
            if len(rubric_scores) == 1:
                rubric_scores_sum = sum(rubric_scores[0])
                log.debug("""Score normalized for location={loc}, old_score={old_score},
                new_score={new_score}, rubric_score={rubric_score}""".format(
                    loc=self.location_string,
                    old_score=score,
                    new_score=rubric_scores_sum,
                    rubric_score=rubric_scores
                ))
                return rubric_scores_sum
        return score


class OpenEndedDescriptor(object):
    """
    Module for adding open ended response questions to courses
    """
    mako_template = "widgets/html-edit.html"
    module_class = OpenEndedModule
    filename_extension = "xml"

    has_score = True

    def __init__(self, system):
        self.system = system

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Pull out the open ended parameters into a dictionary.

        Returns:
        {
        'oeparam': 'some-html'
        }
        """
        for child in ['openendedparam']:
            if len(xml_object.xpath(child)) != 1:
                # This is a staff_facing_error
                raise ValueError(
                    u"Open Ended definition must include exactly one '{0}' tag. Contact the learning sciences group for assistance.".format(
                        child))

        def parse(k):
            """Assumes that xml_object has child k"""
            return xml_object.xpath(k)[0]

        return {
            'oeparam': parse('openendedparam')
        }

    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        elt = etree.Element('openended')

        def add_child(k):
            child_str = u'<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            elt.append(child_node)

        for child in ['openendedparam']:
            add_child(child)

        return elt
