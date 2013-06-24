import cgi
import datetime
import hashlib
import json
import logging
import os
import traceback
import struct
import sys

from pkg_resources import resource_string

from capa.capa_problem import LoncapaProblem
from capa.responsetypes import StudentInputError, \
    ResponseError, LoncapaProblemError
from capa.util import convert_files_to_filenames
from .progress import Progress
from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.exceptions import NotFoundError, ProcessingError
from xblock.core import Scope, String, Boolean, Dict, Integer, Float
from .fields import Timedelta, Date
from django.utils.timezone import UTC

log = logging.getLogger("mitx.courseware")


# Generate this many different variants of problems with rerandomize=per_student
NUM_RANDOMIZATION_BINS = 20
# Never produce more than this many different seeds, no matter what.
MAX_RANDOMIZATION_BINS = 1000


def randomization_bin(seed, problem_id):
    """
    Pick a randomization bin for the problem given the user's seed and a problem id.

    We do this because we only want e.g. 20 randomizations of a problem to make analytics
    interesting.  To avoid having sets of students that always get the same problems,
    we'll combine the system's per-student seed with the problem id in picking the bin.
    """
    h = hashlib.sha1()
    h.update(str(seed))
    h.update(str(problem_id))
    # get the first few digits of the hash, convert to an int, then mod.
    return int(h.hexdigest()[:7], 16) % NUM_RANDOMIZATION_BINS


class Randomization(String):
    def from_json(self, value):
        if value in ("", "true"):
            return "always"
        elif value == "false":
            return "per_student"
        return value

    to_json = from_json


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, complex):
            return "{real:.7g}{imag:+.7g}*j".format(real=obj.real, imag=obj.imag)
        return json.JSONEncoder.default(self, obj)


class CapaFields(object):
    attempts = Integer(help="Number of attempts taken by the student on this problem", default=0, scope=Scope.user_state)
    max_attempts = Integer(
        display_name="Maximum Attempts",
        help="Defines the number of times a student can try to answer this problem. If the value is not set, infinite attempts are allowed.",
        values={"min": 0}, scope=Scope.settings
    )
    due = Date(help="Date that this problem is due by", scope=Scope.settings)
    graceperiod = Timedelta(help="Amount of time after the due date that submissions will be accepted", scope=Scope.settings)
    showanswer = String(
        display_name="Show Answer",
        help="Defines when to show the answer to the problem. A default value can be set in Advanced Settings.",
        scope=Scope.settings, default="closed",
        values=[
            {"display_name": "Always", "value": "always"},
            {"display_name": "Answered", "value": "answered"},
            {"display_name": "Attempted", "value": "attempted"},
            {"display_name": "Closed", "value": "closed"},
            {"display_name": "Finished", "value": "finished"},
            {"display_name": "Past Due", "value": "past_due"},
            {"display_name": "Never", "value": "never"}]
    )
    force_save_button = Boolean(help="Whether to force the save button to appear on the page", scope=Scope.settings, default=False)
    rerandomize = Randomization(
        display_name="Randomization", help="Defines how often inputs are randomized when a student loads the problem. This setting only applies to problems that can have randomly generated numeric values. A default value can be set in Advanced Settings.",
        default="always", scope=Scope.settings, values=[{"display_name": "Always", "value": "always"},
                                                        {"display_name": "On Reset", "value": "onreset"},
                                                        {"display_name": "Never", "value": "never"},
                                                        {"display_name": "Per Student", "value": "per_student"}]
    )
    data = String(help="XML data for the problem", scope=Scope.content)
    correct_map = Dict(help="Dictionary with the correctness of current student answers", scope=Scope.user_state, default={})
    input_state = Dict(help="Dictionary for maintaining the state of inputtypes", scope=Scope.user_state)
    student_answers = Dict(help="Dictionary with the current student responses", scope=Scope.user_state)
    done = Boolean(help="Whether the student has answered the problem", scope=Scope.user_state)
    seed = Integer(help="Random seed for this student", scope=Scope.user_state)
    weight = Float(
        display_name="Problem Weight",
        help="Defines the number of points each problem is worth. If the value is not set, each response field in the problem is worth one point.",
        values={"min": 0, "step": .1},
        scope=Scope.settings
    )
    markdown = String(help="Markdown source of this module", scope=Scope.settings)
    source_code = String(
        help="Source code for LaTeX and Word problems. This feature is not well-supported.",
        scope=Scope.settings
    )


class CapaModule(CapaFields, XModule):
    '''
    An XModule implementing LonCapa format problems, implemented by way of
    capa.capa_problem.LoncapaProblem

    CapaModule.__init__ takes the same arguments as xmodule.x_module:XModule.__init__
    '''
    icon_class = 'problem'

    js = {'coffee': [resource_string(__name__, 'js/src/capa/display.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     ],
          'js': [resource_string(__name__, 'js/src/capa/imageinput.js'),
                 resource_string(__name__, 'js/src/capa/schematic.js')
                 ]}

    js_module_name = "Problem"
    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}

    def __init__(self, *args, **kwargs):
        """ Accepts the same arguments as xmodule.x_module:XModule.__init__ """
        XModule.__init__(self, *args, **kwargs)

        due_date = self.due

        if self.graceperiod is not None and due_date:
            self.close_date = due_date + self.graceperiod
        else:
            self.close_date = due_date

        if self.seed is None:
            self.choose_new_seed()

        # Need the problem location in openendedresponse to send out.  Adding
        # it to the system here seems like the least clunky way to get it
        # there.
        self.system.set('location', self.location.url())

        try:
            # TODO (vshnayder): move as much as possible of this work and error
            # checking to descriptor load time
            self.lcp = self.new_lcp(self.get_state_for_lcp())

            # At this point, we need to persist the randomization seed
            # so that when the problem is re-loaded (to check/view/save)
            # it stays the same.
            # However, we do not want to write to the database
            # every time the module is loaded.
            # So we set the seed ONLY when there is not one set already
            if self.seed is None:
                self.seed = self.lcp.seed

        except Exception as err:
            msg = 'cannot create LoncapaProblem {loc}: {err}'.format(
                loc=self.location.url(), err=err)
            # TODO (vshnayder): do modules need error handlers too?
            # We shouldn't be switching on DEBUG.
            if self.system.DEBUG:
                log.warning(msg)
                # TODO (vshnayder): This logic should be general, not here--and may
                # want to preserve the data instead of replacing it.
                # e.g. in the CMS
                msg = '<p>%s</p>' % msg.replace('<', '&lt;')
                msg += '<p><pre>%s</pre></p>' % traceback.format_exc().replace('<', '&lt;')
                # create a dummy problem with error message instead of failing
                problem_text = ('<problem><text><span class="inline-error">'
                                'Problem %s has an error:</span>%s</text></problem>' %
                                (self.location.url(), msg))
                self.lcp = self.new_lcp(self.get_state_for_lcp(), text=problem_text)
            else:
                # add extra info and raise
                raise Exception(msg), None, sys.exc_info()[2]

            self.set_state_from_lcp()

        assert self.seed is not None

    def choose_new_seed(self):
        """Choose a new seed."""
        if self.rerandomize == 'never':
            self.seed = 1
        elif self.rerandomize == "per_student" and hasattr(self.system, 'seed'):
            # see comment on randomization_bin
            self.seed = randomization_bin(self.system.seed, self.location.url)
        else:
            self.seed = struct.unpack('i', os.urandom(4))[0]

            # So that sandboxed code execution can be cached, but still have an interesting
            # number of possibilities, cap the number of different random seeds.
            self.seed %= MAX_RANDOMIZATION_BINS

    def new_lcp(self, state, text=None):
        if text is None:
            text = self.data

        return LoncapaProblem(
            problem_text=text,
            id=self.location.html_id(),
            state=state,
            seed=self.seed,
            system=self.system,
        )

    def get_state_for_lcp(self):
        return {
            'done': self.done,
            'correct_map': self.correct_map,
            'student_answers': self.student_answers,
            'input_state': self.input_state,
            'seed': self.seed,
        }

    def set_state_from_lcp(self):
        lcp_state = self.lcp.get_state()
        self.done = lcp_state['done']
        self.correct_map = lcp_state['correct_map']
        self.input_state = lcp_state['input_state']
        self.student_answers = lcp_state['student_answers']
        self.seed = lcp_state['seed']

    def get_score(self):
        return self.lcp.get_score()

    def max_score(self):
        return self.lcp.get_max_score()

    def get_progress(self):
        ''' For now, just return score / max_score
        '''
        d = self.get_score()
        score = d['score']
        total = d['total']
        if total > 0:
            try:
                return Progress(score, total)
            except Exception:
                log.exception("Got bad progress")
                return None
        return None

    def get_html(self):
        return self.system.render_template('problem_ajax.html', {
            'element_id': self.location.html_id(),
            'id': self.id,
            'ajax_url': self.system.ajax_url,
            'progress': Progress.to_js_status_str(self.get_progress())
        })

    def check_button_name(self):
        """
        Determine the name for the "check" button.
        Usually it is just "Check", but if this is the student's
        final attempt, change the name to "Final Check"
        """
        if self.max_attempts is not None:
            final_check = (self.attempts >= self.max_attempts - 1)
        else:
            final_check = False

        return "Final Check" if final_check else "Check"

    def should_show_check_button(self):
        """
        Return True/False to indicate whether to show the "Check" button.
        """
        submitted_without_reset = (self.is_submitted() and self.rerandomize == "always")

        # If the problem is closed (past due / too many attempts)
        # then we do NOT show the "check" button
        # Also, do not show the "check" button if we're waiting
        # for the user to reset a randomized problem
        if self.closed() or submitted_without_reset:
            return False
        else:
            return True

    def should_show_reset_button(self):
        """
        Return True/False to indicate whether to show the "Reset" button.
        """
        is_survey_question = (self.max_attempts == 0)

        if self.rerandomize in ["always", "onreset"]:

            # If the problem is closed (and not a survey question with max_attempts==0),
            # then do NOT show the reset button.
            # If the problem hasn't been submitted yet, then do NOT show
            # the reset button.
            if (self.closed() and not is_survey_question) or not self.is_submitted():
                return False
            else:
                return True
        # Only randomized problems need a "reset" button
        else:
            return False

    def should_show_save_button(self):
        """
        Return True/False to indicate whether to show the "Save" button.
        """

        # If the user has forced the save button to display,
        # then show it as long as the problem is not closed
        # (past due / too many attempts)
        if self.force_save_button:
            return not self.closed()
        else:
            is_survey_question = (self.max_attempts == 0)
            needs_reset = self.is_submitted() and self.rerandomize == "always"

            # If the student has unlimited attempts, and their answers
            # are not randomized, then we do not need a save button
            # because they can use the "Check" button without consequences.
            #
            # The consequences we want to avoid are:
            # * Using up an attempt (if max_attempts is set)
            # * Changing the current problem, and no longer being
            #   able to view it (if rerandomize is "always")
            #
            # In those cases. the if statement below is false,
            # and the save button can still be displayed.
            #
            if self.max_attempts is None and self.rerandomize != "always":
                return False

            # If the problem is closed (and not a survey question with max_attempts==0),
            # then do NOT show the save button
            # If we're waiting for the user to reset a randomized problem
            # then do NOT show the save button
            elif (self.closed() and not is_survey_question) or needs_reset:
                return False
            else:
                return True

    def handle_problem_html_error(self, err):
        """
        Change our problem to a dummy problem containing
        a warning message to display to users.

        Returns the HTML to show to users

        *err* is the Exception encountered while rendering the problem HTML.
        """
        log.exception(err)

        # TODO (vshnayder): another switch on DEBUG.
        if self.system.DEBUG:
            msg = (
                '[courseware.capa.capa_module] <font size="+1" color="red">'
                'Failed to generate HTML for problem %s</font>' %
                (self.location.url()))
            msg += '<p>Error:</p><p><pre>%s</pre></p>' % str(err).replace('<', '&lt;')
            msg += '<p><pre>%s</pre></p>' % traceback.format_exc().replace('<', '&lt;')
            html = msg

        # We're in non-debug mode, and possibly even in production. We want
        #   to avoid bricking of problem as much as possible
        else:
            # We're in non-debug mode, and possibly even in production. We want
            #   to avoid bricking of problem as much as possible

            # Presumably, student submission has corrupted LoncapaProblem HTML.
            #   First, pull down all student answers
            student_answers = self.lcp.student_answers
            answer_ids = student_answers.keys()

            # Some inputtypes, such as dynamath, have additional "hidden" state that
            #   is not exposed to the student. Keep those hidden
            # TODO: Use regex, e.g. 'dynamath' is suffix at end of answer_id
            hidden_state_keywords = ['dynamath']
            for answer_id in answer_ids:
                for hidden_state_keyword in hidden_state_keywords:
                    if answer_id.find(hidden_state_keyword) >= 0:
                        student_answers.pop(answer_id)

            #   Next, generate a fresh LoncapaProblem
            self.lcp = self.new_lcp(None)
            self.set_state_from_lcp()

            # Prepend a scary warning to the student
            warning = '<div class="capa_reset">'\
                      '<h2>Warning: The problem has been reset to its initial state!</h2>'\
                      'The problem\'s state was corrupted by an invalid submission. ' \
                      'The submission consisted of:'\
                      '<ul>'
            for student_answer in student_answers.values():
                if student_answer != '':
                    warning += '<li>' + cgi.escape(student_answer) + '</li>'
            warning += '</ul>'\
                       'If this error persists, please contact the course staff.'\
                       '</div>'

            html = warning
            try:
                html += self.lcp.get_html()
            except Exception:  # Couldn't do it. Give up
                log.exception("Unable to generate html from LoncapaProblem")
                raise

        return html

    def get_problem_html(self, encapsulate=True):
        '''Return html for the problem.  Adds check, reset, save buttons
        as necessary based on the problem config and state.'''

        try:
            html = self.lcp.get_html()

        # If we cannot construct the problem HTML,
        # then generate an error message instead.
        except Exception as err:
            html = self.handle_problem_html_error(err)

        # The convention is to pass the name of the check button
        # if we want to show a check button, and False otherwise
        # This works because non-empty strings evaluate to True
        if self.should_show_check_button():
            check_button = self.check_button_name()
        else:
            check_button = False

        content = {'name': self.display_name_with_default,
                   'html': html,
                   'weight': self.weight,
                   }

        context = {'problem': content,
                   'id': self.id,
                   'check_button': check_button,
                   'reset_button': self.should_show_reset_button(),
                   'save_button': self.should_show_save_button(),
                   'answer_available': self.answer_available(),
                   'ajax_url': self.system.ajax_url,
                   'attempts_used': self.attempts,
                   'attempts_allowed': self.max_attempts,
                   'progress': self.get_progress(),
                   }

        html = self.system.render_template('problem.html', context)
        if encapsulate:
            html = '<div id="problem_{id}" class="problem" data-url="{ajax_url}">'.format(
                id=self.location.html_id(), ajax_url=self.system.ajax_url) + html + "</div>"

        # now do the substitutions which are filesystem based, e.g. '/static/' prefixes
        return self.system.replace_urls(html)

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
            'problem_check': self.check_problem,
            'problem_reset': self.reset_problem,
            'problem_save': self.save_problem,
            'problem_show': self.get_answer,
            'score_update': self.update_score,
            'input_ajax': self.handle_input_ajax,
            'ungraded_response': self.handle_ungraded_response
        }

        if dispatch not in handlers:
            return 'Error'

        before = self.get_progress()

        try:
            d = handlers[dispatch](get)

        except Exception as err:
            _, _, traceback_obj = sys.exc_info()
            raise ProcessingError, err.message, traceback_obj

        after = self.get_progress()
        d.update({
            'progress_changed': after != before,
            'progress_status': Progress.to_js_status_str(after),
        })
        return json.dumps(d, cls=ComplexEncoder)

    def is_past_due(self):
        """
        Is it now past this problem's due date, including grace period?
        """
        return (self.close_date is not None and
                datetime.datetime.now(UTC()) > self.close_date)

    def closed(self):
        ''' Is the student still allowed to submit answers? '''
        if self.max_attempts is not None and self.attempts >= self.max_attempts:
            return True
        if self.is_past_due():
            return True

        return False

    def is_submitted(self):
        """
        Used to decide to show or hide RESET or CHECK buttons.

        Means that student submitted problem and nothing more.
        Problem can be completely wrong.
        Pressing RESET button makes this function to return False.
        """
        return self.lcp.done

    def is_attempted(self):
        """Used by conditional module"""
        return self.attempts > 0

    def is_correct(self):
        """True if full points"""
        d = self.get_score()
        return d['score'] == d['total']

    def answer_available(self):
        '''
        Is the user allowed to see an answer?
        '''
        if self.showanswer == '':
            return False
        elif self.showanswer == "never":
            return False
        elif self.system.user_is_staff:
            # This is after the 'never' check because admins can see the answer
            # unless the problem explicitly prevents it
            return True
        elif self.showanswer == 'attempted':
            return self.attempts > 0
        elif self.showanswer == 'answered':
            # NOTE: this is slightly different from 'attempted' -- resetting the problems
            # makes lcp.done False, but leaves attempts unchanged.
            return self.lcp.done
        elif self.showanswer == 'closed':
            return self.closed()
        elif self.showanswer == 'finished':
            return self.closed() or self.is_correct()

        elif self.showanswer == 'past_due':
            return self.is_past_due()
        elif self.showanswer == 'always':
            return True

        return False

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
        self.lcp.update_score(score_msg, queuekey)
        self.set_state_from_lcp()
        self.publish_grade()

        return dict()  # No AJAX return is needed

    def handle_ungraded_response(self, get):
        '''
        Delivers a response from the XQueue to the capa problem

        The score of the problem will not be updated

        Args:
            - get (dict) must contain keys:
                            queuekey - a key specific to this response
                            xqueue_body - the body of the response
        Returns:
            empty dictionary

        No ajax return is needed, so an empty dict is returned
        '''
        queuekey = get['queuekey']
        score_msg = get['xqueue_body']
        # pass along the xqueue message to the problem
        self.lcp.ungraded_response(score_msg, queuekey)
        self.set_state_from_lcp()
        return dict()

    def handle_input_ajax(self, get):
        '''
        Handle ajax calls meant for a particular input in the problem

        Args:
            - get (dict) - data that should be passed to the input
        Returns:
            - dict containing the response from the input
        '''
        response = self.lcp.handle_input_ajax(get)
        # save any state changes that may occur
        self.set_state_from_lcp()
        return response

    def get_answer(self, get):
        '''
        For the "show answer" button.

        Returns the answers: {'answers' : answers}
        '''
        event_info = dict()
        event_info['problem_id'] = self.location.url()
        self.system.track_function('showanswer', event_info)
        if not self.answer_available():
            raise NotFoundError('Answer is not available')
        else:
            answers = self.lcp.get_question_answers()
            self.set_state_from_lcp()

        # answers (eg <solution>) may have embedded images
        #   but be careful, some problems are using non-string answer dicts
        new_answers = dict()
        for answer_id in answers:
            try:
                new_answer = {answer_id: self.system.replace_urls(answers[answer_id])}
            except TypeError:
                log.debug('Unable to perform URL substitution on answers[%s]: %s' % (answer_id, answers[answer_id]))
                new_answer = {answer_id: answers[answer_id]}
            new_answers.update(new_answer)

        return {'answers': new_answers}

    # Figure out if we should move these to capa_problem?
    def get_problem(self, get):
        ''' Return results of get_problem_html, as a simple dict for json-ing.
        { 'html': <the-html> }

            Used if we want to reconfirm we have the right thing e.g. after
            several AJAX calls.
        '''
        return {'html': self.get_problem_html(encapsulate=False)}

    @staticmethod
    def make_dict_of_responses(get):
        '''Make dictionary of student responses (aka "answers")
        get is POST dictionary (Django QueryDict).

        The *get* dict has keys of the form 'x_y', which are mapped
        to key 'y' in the returned dict.  For example,
        'input_1_2_3' would be mapped to '1_2_3' in the returned dict.

        Some inputs always expect a list in the returned dict
        (e.g. checkbox inputs).  The convention is that
        keys in the *get* dict that end with '[]' will always
        have list values in the returned dict.
        For example, if the *get* dict contains {'input_1[]': 'test' }
        then the output dict would contain {'1': ['test'] }
        (the value is a list).

        Raises an exception if:

            A key in the *get* dictionary does not contain >= 1 underscores
            (e.g. "input" is invalid; "input_1" is valid)

            Two keys end up with the same name in the returned dict.
            (e.g. 'input_1' and 'input_1[]', which both get mapped
            to 'input_1' in the returned dict)
        '''
        answers = dict()

        for key in get:
            # e.g. input_resistor_1 ==> resistor_1
            _, _, name = key.partition('_')

            # If key has no underscores, then partition
            # will return (key, '', '')
            # We detect this and raise an error
            if not name:
                raise ValueError("%s must contain at least one underscore" % str(key))

            else:
                # This allows for answers which require more than one value for
                # the same form input (e.g. checkbox inputs). The convention is that
                # if the name ends with '[]' (which looks like an array), then the
                # answer will be an array.
                is_list_key = name.endswith('[]')
                name = name[:-2] if is_list_key else name

                if is_list_key:
                    val = get.getlist(key)
                else:
                    val = get[key]

                # If the name already exists, then we don't want
                # to override it.  Raise an error instead
                if name in answers:
                    raise ValueError("Key %s already exists in answers dict" % str(name))
                else:
                    answers[name] = val

        return answers

    def publish_grade(self):
        """
        Publishes the student's current grade to the system as an event
        """
        score = self.lcp.get_score()
        self.system.publish({
            'event_name': 'grade',
            'value': score['score'],
            'max_value': score['total'],
        })

    def check_problem(self, get):
        ''' Checks whether answers to a problem are correct, and
            returns a map of correct/incorrect answers:

            {'success' : 'correct' | 'incorrect' | AJAX alert msg string,
             'contents' : html}
            '''
        event_info = dict()
        event_info['state'] = self.lcp.get_state()
        event_info['problem_id'] = self.location.url()

        answers = self.make_dict_of_responses(get)
        event_info['answers'] = convert_files_to_filenames(answers)
        # Too late. Cannot submit
        if self.closed():
            event_info['failure'] = 'closed'
            self.system.track_function('problem_check_fail', event_info)
            raise NotFoundError('Problem is closed')

        # Problem submitted. Student should reset before checking again
        if self.done and self.rerandomize == "always":
            event_info['failure'] = 'unreset'
            self.system.track_function('problem_check_fail', event_info)
            raise NotFoundError('Problem must be reset before it can be checked again')

        # Problem queued. Students must wait a specified waittime before they are allowed to submit
        if self.lcp.is_queued():
            current_time = datetime.datetime.now(UTC())
            prev_submit_time = self.lcp.get_recentmost_queuetime()
            waittime_between_requests = self.system.xqueue['waittime']
            if (current_time - prev_submit_time).total_seconds() < waittime_between_requests:
                msg = 'You must wait at least %d seconds between submissions' % waittime_between_requests
                return {'success': msg, 'html': ''}  # Prompts a modal dialog in ajax callback

        try:
            correct_map = self.lcp.grade_answers(answers)
            self.attempts = self.attempts + 1
            self.lcp.done = True
            self.set_state_from_lcp()

        except (StudentInputError, ResponseError, LoncapaProblemError) as inst:
            log.warning("StudentInputError in capa_module:problem_check",
                        exc_info=True)

            # If the user is a staff member, include
            # the full exception, including traceback,
            # in the response
            if self.system.user_is_staff:
                msg = "Staff debug info: %s" % traceback.format_exc()

            # Otherwise, display just an error message,
            # without a stack trace
            else:
                msg = "Error: %s" % str(inst.message)

            return {'success': msg}

        except Exception as err:
            if self.system.DEBUG:
                msg = "Error checking problem: " + str(err)
                msg += '\nTraceback:\n' + traceback.format_exc()
                return {'success': msg}
            raise

        self.publish_grade()

        # success = correct if ALL questions in this problem are correct
        success = 'correct'
        for answer_id in correct_map:
            if not correct_map.is_correct(answer_id):
                success = 'incorrect'

        # NOTE: We are logging both full grading and queued-grading submissions. In the latter,
        #       'success' will always be incorrect
        event_info['correct_map'] = correct_map.get_dict()
        event_info['success'] = success
        event_info['attempts'] = self.attempts
        self.system.track_function('problem_check', event_info)

        if hasattr(self.system, 'psychometrics_handler'):  # update PsychometricsData using callback
            self.system.psychometrics_handler(self.get_state_for_lcp())

        # render problem into HTML
        html = self.get_problem_html(encapsulate=False)

        return {'success': success,
                'contents': html,
                }

    def rescore_problem(self):
        """
        Checks whether the existing answers to a problem are correct.

        This is called when the correct answer to a problem has been changed,
        and the grade should be re-evaluated.

        Returns a dict with one key:
            {'success' : 'correct' | 'incorrect' | AJAX alert msg string }

        Raises NotFoundError if called on a problem that has not yet been
        answered, or NotImplementedError if it's a problem that cannot be rescored.

        Returns the error messages for exceptions occurring while performing
        the rescoring, rather than throwing them.
        """
        event_info = {'state': self.lcp.get_state(), 'problem_id': self.location.url()}

        if not self.lcp.supports_rescoring():
            event_info['failure'] = 'unsupported'
            self.system.track_function('problem_rescore_fail', event_info)
            raise NotImplementedError("Problem's definition does not support rescoring")

        if not self.done:
            event_info['failure'] = 'unanswered'
            self.system.track_function('problem_rescore_fail', event_info)
            raise NotFoundError('Problem must be answered before it can be graded again')

        # get old score, for comparison:
        orig_score = self.lcp.get_score()
        event_info['orig_score'] = orig_score['score']
        event_info['orig_total'] = orig_score['total']

        try:
            correct_map = self.lcp.rescore_existing_answers()

        except (StudentInputError, ResponseError, LoncapaProblemError) as inst:
            log.warning("Input error in capa_module:problem_rescore", exc_info=True)
            event_info['failure'] = 'input_error'
            self.system.track_function('problem_rescore_fail', event_info)
            return {'success': u"Error: {0}".format(inst.message)}

        except Exception as err:
            event_info['failure'] = 'unexpected'
            self.system.track_function('problem_rescore_fail', event_info)
            if self.system.DEBUG:
                msg = u"Error checking problem: {0}".format(err.message)
                msg += u'\nTraceback:\n' + traceback.format_exc()
                return {'success': msg}
            raise

        # rescoring should have no effect on attempts, so don't
        # need to increment here, or mark done.  Just save.
        self.set_state_from_lcp()

        self.publish_grade()

        new_score = self.lcp.get_score()
        event_info['new_score'] = new_score['score']
        event_info['new_total'] = new_score['total']

        # success = correct if ALL questions in this problem are correct
        success = 'correct'
        for answer_id in correct_map:
            if not correct_map.is_correct(answer_id):
                success = 'incorrect'

        # NOTE: We are logging both full grading and queued-grading submissions. In the latter,
        #       'success' will always be incorrect
        event_info['correct_map'] = correct_map.get_dict()
        event_info['success'] = success
        event_info['attempts'] = self.attempts
        self.system.track_function('problem_rescore', event_info)

        # psychometrics should be called on rescoring requests in the same way as check-problem
        if hasattr(self.system, 'psychometrics_handler'):  # update PsychometricsData using callback
            self.system.psychometrics_handler(self.get_state_for_lcp())

        return {'success': success}

    def save_problem(self, get):
        """
        Save the passed in answers.
        Returns a dict { 'success' : bool, 'msg' : message }
        The message is informative on success, and an error message on failure.
        """
        event_info = dict()
        event_info['state'] = self.lcp.get_state()
        event_info['problem_id'] = self.location.url()

        answers = self.make_dict_of_responses(get)
        event_info['answers'] = answers

        # Too late. Cannot submit
        if self.closed() and not self.max_attempts == 0:
            event_info['failure'] = 'closed'
            self.system.track_function('save_problem_fail', event_info)
            return {'success': False,
                    'msg': "Problem is closed"}

        # Problem submitted. Student should reset before saving
        # again.
        if self.done and self.rerandomize == "always":
            event_info['failure'] = 'done'
            self.system.track_function('save_problem_fail', event_info)
            return {'success': False,
                    'msg': "Problem needs to be reset prior to save"}

        self.lcp.student_answers = answers

        self.set_state_from_lcp()

        self.system.track_function('save_problem_success', event_info)
        msg = "Your answers have been saved"
        if not self.max_attempts == 0:
            msg += " but not graded. Hit 'Check' to grade them."
        return {'success': True,
                'msg': msg}

    def reset_problem(self, get):
        ''' Changes problem state to unfinished -- removes student answers,
            and causes problem to rerender itself.

            Returns a dictionary of the form:
            {'success': True/False,
            'html': Problem HTML string }

            If an error occurs, the dictionary will also have an
            'error' key containing an error message.
        '''
        event_info = dict()
        event_info['old_state'] = self.lcp.get_state()
        event_info['problem_id'] = self.location.url()

        if self.closed():
            event_info['failure'] = 'closed'
            self.system.track_function('reset_problem_fail', event_info)
            return {'success': False,
                    'error': "Problem is closed"}

        if not self.done:
            event_info['failure'] = 'not_done'
            self.system.track_function('reset_problem_fail', event_info)
            return {'success': False,
                    'error': "Refresh the page and make an attempt before resetting."}

        if self.rerandomize in ["always", "onreset"]:
            # Reset random number generator seed.
            self.choose_new_seed()

        # Generate a new problem with either the previous seed or a new seed
        self.lcp = self.new_lcp(None)

        # Pull in the new problem seed
        self.set_state_from_lcp()

        event_info['new_state'] = self.lcp.get_state()
        self.system.track_function('reset_problem', event_info)

        return {'success': True,
                'html': self.get_problem_html(encapsulate=False)}


class CapaDescriptor(CapaFields, RawDescriptor):
    """
    Module implementing problems in the LON-CAPA format,
    as implemented by capa.capa_problem
    """

    module_class = CapaModule

    has_score = True
    template_dir_name = 'problem'
    mako_template = "widgets/problem-edit.html"
    js = {'coffee': [resource_string(__name__, 'js/src/problem/edit.coffee')]}
    js_module_name = "MarkdownEditingDescriptor"
    css = {'scss': [resource_string(__name__, 'css/editor/edit.scss'), resource_string(__name__, 'css/problem/edit.scss')]}

    # Capa modules have some additional metadata:
    # TODO (vshnayder): do problems have any other metadata?  Do they
    # actually use type and points?
    metadata_attributes = RawDescriptor.metadata_attributes + ('type', 'points')

    # The capa format specifies that what we call max_attempts in the code
    # is the attribute `attempts`. This will do that conversion
    metadata_translations = dict(RawDescriptor.metadata_translations)
    metadata_translations['attempts'] = 'max_attempts'

    def get_context(self):
        _context = RawDescriptor.get_context(self)
        _context.update({'markdown': self.markdown,
                         'enable_markdown': self.markdown is not None})
        return _context

    # VS[compat]
    # TODO (cpennington): Delete this method once all fall 2012 course are being
    # edited in the cms
    @classmethod
    def backcompat_paths(cls, path):
        return [
            'problems/' + path[8:],
            path[8:],
        ]

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(CapaDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([CapaDescriptor.due, CapaDescriptor.graceperiod,
                                    CapaDescriptor.force_save_button, CapaDescriptor.markdown])
        return non_editable_fields
