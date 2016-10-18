"""Implements basics of Capa, including class CapaModule."""
import cgi
import copy
import datetime
import hashlib
import json
import logging
import os
import traceback
import struct
import sys
import re

# We don't want to force a dependency on datadog, so make the import conditional
try:
    import dogstats_wrapper as dog_stats_api
except ImportError:
    dog_stats_api = None

from capa.capa_problem import LoncapaProblem, LoncapaSystem
from capa.responsetypes import StudentInputError, \
    ResponseError, LoncapaProblemError
from capa.util import convert_files_to_filenames, get_inner_html_from_xpath
from .progress import Progress
from xmodule.exceptions import NotFoundError
from xblock.fields import Scope, String, Boolean, Dict, Integer, Float
from .fields import Timedelta, Date
from django.utils.timezone import UTC
from xmodule.capa_base_constants import RANDOMIZATION, SHOWANSWER
from django.conf import settings

from openedx.core.djangolib.markup import HTML, Text

log = logging.getLogger("edx.courseware")

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text

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
    r_hash = hashlib.sha1()
    r_hash.update(str(seed))
    r_hash.update(str(problem_id))
    # get the first few digits of the hash, convert to an int, then mod.
    return int(r_hash.hexdigest()[:7], 16) % NUM_RANDOMIZATION_BINS


class Randomization(String):
    """
    Define a field to store how to randomize a problem.
    """
    def from_json(self, value):
        if value in ("", "true"):
            return RANDOMIZATION.ALWAYS
        elif value == "false":
            return RANDOMIZATION.PER_STUDENT
        return value

    to_json = from_json


class ComplexEncoder(json.JSONEncoder):
    """
    Extend the JSON encoder to correctly handle complex numbers
    """
    def default(self, obj):
        """
        Print a nicely formatted complex number, or default to the JSON encoder
        """
        if isinstance(obj, complex):
            return u"{real:.7g}{imag:+.7g}*j".format(real=obj.real, imag=obj.imag)
        return json.JSONEncoder.default(self, obj)


class CapaFields(object):
    """
    Define the possible fields for a Capa problem
    """
    display_name = String(
        display_name=_("Display Name"),
        help=_("This name appears in the horizontal navigation at the top of the page."),
        scope=Scope.settings,
        # it'd be nice to have a useful default but it screws up other things; so,
        # use display_name_with_default for those
        default=_("Blank Advanced Problem")
    )
    attempts = Integer(
        help=_("Number of attempts taken by the student on this problem"),
        default=0,
        scope=Scope.user_state)
    max_attempts = Integer(
        display_name=_("Maximum Attempts"),
        help=_("Defines the number of times a student can try to answer this problem. "
               "If the value is not set, infinite attempts are allowed."),
        values={"min": 0}, scope=Scope.settings
    )
    due = Date(help=_("Date that this problem is due by"), scope=Scope.settings)
    graceperiod = Timedelta(
        help=_("Amount of time after the due date that submissions will be accepted"),
        scope=Scope.settings
    )
    showanswer = String(
        display_name=_("Show Answer"),
        help=_("Defines when to show the answer to the problem. "
               "A default value can be set in Advanced Settings."),
        scope=Scope.settings,
        default=SHOWANSWER.FINISHED,
        values=[
            {"display_name": _("Always"), "value": SHOWANSWER.ALWAYS},
            {"display_name": _("Answered"), "value": SHOWANSWER.ANSWERED},
            {"display_name": _("Attempted"), "value": SHOWANSWER.ATTEMPTED},
            {"display_name": _("Closed"), "value": SHOWANSWER.CLOSED},
            {"display_name": _("Finished"), "value": SHOWANSWER.FINISHED},
            {"display_name": _("Correct or Past Due"), "value": SHOWANSWER.CORRECT_OR_PAST_DUE},
            {"display_name": _("Past Due"), "value": SHOWANSWER.PAST_DUE},
            {"display_name": _("Never"), "value": SHOWANSWER.NEVER}]
    )
    force_save_button = Boolean(
        help=_("Whether to force the save button to appear on the page"),
        scope=Scope.settings,
        default=False
    )
    reset_key = "DEFAULT_SHOW_RESET_BUTTON"
    default_reset_button = getattr(settings, reset_key) if hasattr(settings, reset_key) else False
    show_reset_button = Boolean(
        display_name=_("Show Reset Button"),
        help=_("Determines whether a 'Reset' button is shown so the user may reset their answer. "
               "A default value can be set in Advanced Settings."),
        scope=Scope.settings,
        default=default_reset_button
    )
    rerandomize = Randomization(
        display_name=_("Randomization"),
        help=_(
            'Defines when to randomize the variables specified in the associated Python script. '
            'For problems that do not randomize values, specify \"Never\". '
        ),
        default=RANDOMIZATION.NEVER,
        scope=Scope.settings,
        values=[
            {"display_name": _("Always"), "value": RANDOMIZATION.ALWAYS},
            {"display_name": _("On Reset"), "value": RANDOMIZATION.ONRESET},
            {"display_name": _("Never"), "value": RANDOMIZATION.NEVER},
            {"display_name": _("Per Student"), "value": RANDOMIZATION.PER_STUDENT}
        ]
    )
    data = String(help=_("XML data for the problem"), scope=Scope.content, default="<problem></problem>")
    correct_map = Dict(help=_("Dictionary with the correctness of current student answers"),
                       scope=Scope.user_state, default={})
    input_state = Dict(help=_("Dictionary for maintaining the state of inputtypes"), scope=Scope.user_state)
    student_answers = Dict(help=_("Dictionary with the current student responses"), scope=Scope.user_state)
    done = Boolean(help=_("Whether the student has answered the problem"), scope=Scope.user_state)
    seed = Integer(help=_("Random seed for this student"), scope=Scope.user_state)
    last_submission_time = Date(help=_("Last submission time"), scope=Scope.user_state)
    submission_wait_seconds = Integer(
        display_name=_("Timer Between Attempts"),
        help=_("Seconds a student must wait between submissions for a problem with multiple attempts."),
        scope=Scope.settings,
        default=0)
    weight = Float(
        display_name=_("Problem Weight"),
        help=_("Defines the number of points each problem is worth. "
               "If the value is not set, each response field in the problem is worth one point."),
        values={"min": 0, "step": .1},
        scope=Scope.settings
    )
    markdown = String(help=_("Markdown source of this module"), default=None, scope=Scope.settings)
    source_code = String(
        help=_("Source code for LaTeX and Word problems. This feature is not well-supported."),
        scope=Scope.settings
    )
    use_latex_compiler = Boolean(
        help=_("Enable LaTeX templates?"),
        default=False,
        scope=Scope.settings
    )
    matlab_api_key = String(
        display_name=_("Matlab API key"),
        help=_("Enter the API key provided by MathWorks for accessing the MATLAB Hosted Service. "
               "This key is granted for exclusive use by this course for the specified duration. "
               "Please do not share the API key with other courses and notify MathWorks immediately "
               "if you believe the key is exposed or compromised. To obtain a key for your course, "
               "or to report an issue, please contact moocsupport@mathworks.com"),
        scope=Scope.settings
    )


class CapaMixin(CapaFields):
    """
        Core logic for Capa Problem, which can be used by XModules or XBlocks.
    """
    def __init__(self, *args, **kwargs):
        super(CapaMixin, self).__init__(*args, **kwargs)

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
        self.runtime.set('location', self.location.to_deprecated_string())

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

        except Exception as err:  # pylint: disable=broad-except
            msg = u'cannot create LoncapaProblem {loc}: {err}'.format(
                loc=self.location.to_deprecated_string(), err=err)
            # TODO (vshnayder): do modules need error handlers too?
            # We shouldn't be switching on DEBUG.
            if self.runtime.DEBUG:
                log.warning(msg)
                # TODO (vshnayder): This logic should be general, not here--and may
                # want to preserve the data instead of replacing it.
                # e.g. in the CMS
                msg = u'<p>{msg}</p>'.format(msg=cgi.escape(msg))
                msg += u'<p><pre>{tb}</pre></p>'.format(
                    # just the traceback, no message - it is already present above
                    tb=cgi.escape(
                        u''.join(
                            ['Traceback (most recent call last):\n'] +
                            traceback.format_tb(sys.exc_info()[2])
                        )
                    )
                )
                # create a dummy problem with error message instead of failing
                problem_text = (u'<problem><text><span class="inline-error">'
                                u'Problem {url} has an error:</span>{msg}</text></problem>'.format(
                                    url=self.location.to_deprecated_string(),
                                    msg=msg)
                                )
                self.lcp = self.new_lcp(self.get_state_for_lcp(), text=problem_text)
            else:
                # add extra info and raise
                raise Exception(msg), None, sys.exc_info()[2]

            self.set_state_from_lcp()

        assert self.seed is not None

    def choose_new_seed(self):
        """
        Choose a new seed.
        """
        if self.rerandomize == RANDOMIZATION.NEVER:
            self.seed = 1
        elif self.rerandomize == RANDOMIZATION.PER_STUDENT and hasattr(self.runtime, 'seed'):
            # see comment on randomization_bin
            self.seed = randomization_bin(self.runtime.seed, unicode(self.location).encode('utf-8'))
        else:
            self.seed = struct.unpack('i', os.urandom(4))[0]

            # So that sandboxed code execution can be cached, but still have an interesting
            # number of possibilities, cap the number of different random seeds.
            self.seed %= MAX_RANDOMIZATION_BINS

    def new_lcp(self, state, text=None):
        """
        Generate a new Loncapa Problem
        """
        if text is None:
            text = self.data

        capa_system = LoncapaSystem(
            ajax_url=self.runtime.ajax_url,
            anonymous_student_id=self.runtime.anonymous_student_id,
            cache=self.runtime.cache,
            can_execute_unsafe_code=self.runtime.can_execute_unsafe_code,
            get_python_lib_zip=self.runtime.get_python_lib_zip,
            DEBUG=self.runtime.DEBUG,
            filestore=self.runtime.filestore,
            i18n=self.runtime.service(self, "i18n"),
            node_path=self.runtime.node_path,
            render_template=self.runtime.render_template,
            seed=self.runtime.seed,      # Why do we do this if we have self.seed?
            STATIC_URL=self.runtime.STATIC_URL,
            xqueue=self.runtime.xqueue,
            matlab_api_key=self.matlab_api_key
        )

        return LoncapaProblem(
            problem_text=text,
            id=self.location.html_id(),
            state=state,
            seed=self.seed,
            capa_system=capa_system,
            capa_module=self,  # njp
        )

    def get_state_for_lcp(self):
        """
        Give a dictionary holding the state of the module
        """
        return {
            'done': self.done,
            'correct_map': self.correct_map,
            'student_answers': self.student_answers,
            'input_state': self.input_state,
            'seed': self.seed,
        }

    def set_state_from_lcp(self):
        """
        Set the module's state from the settings in `self.lcp`
        """
        lcp_state = self.lcp.get_state()
        self.done = lcp_state['done']
        self.correct_map = lcp_state['correct_map']
        self.input_state = lcp_state['input_state']
        self.student_answers = lcp_state['student_answers']
        self.seed = lcp_state['seed']

    def set_last_submission_time(self):
        """
        Set the module's last submission time (when the problem was submitted)
        """
        self.last_submission_time = datetime.datetime.now(UTC())

    def get_score(self):
        """
        Access the problem's score
        """
        return self.lcp.get_score()

    def max_score(self):
        """
        Access the problem's max score
        """
        return self.lcp.get_max_score()

    def get_progress(self):
        """
        For now, just return score / max_score
        """
        score_dict = self.get_score()
        score = score_dict['score']
        total = score_dict['total']

        if total > 0:
            if self.weight is not None:
                # Progress objects expect total > 0
                if self.weight == 0:
                    return None

                # scale score and total by weight/total:
                score = score * self.weight / total
                total = self.weight

            try:
                return Progress(score, total)
            except (TypeError, ValueError):
                log.exception("Got bad progress")
                return None
        return None

    def get_html(self):
        """
        Return some html with data about the module
        """
        progress = self.get_progress()
        curr_score, total_possible = (progress.frac() if progress else (0, 0))
        return self.runtime.render_template('problem_ajax.html', {
            'element_id': self.location.html_id(),
            'id': self.location.to_deprecated_string(),
            'ajax_url': self.runtime.ajax_url,
            'current_score': curr_score,
            'total_possible': total_possible,
            'attempts_used': self.attempts,
            'content': self.get_problem_html(encapsulate=False),
            'graded': self.graded,
        })

    def submit_button_name(self):
        """
        Determine the name for the "submit" button.
        """
        # The logic flow is a little odd so that _('xxx') strings can be found for
        # translation while also running _() just once for each string.
        _ = self.runtime.service(self, "i18n").ugettext
        submit = _('Submit')

        return submit

    def submit_button_submitting_name(self):
        """
        Return the "Submitting" text for the "submit" button.

        After the user presses the "submit" button, the button will briefly
        display the value returned by this function until a response is
        received by the server.
        """
        _ = self.runtime.service(self, "i18n").ugettext
        return _('Submitting')

    def should_enable_submit_button(self):
        """
        Return True/False to indicate whether to enable the "Submit" button.
        """
        submitted_without_reset = (self.is_submitted() and self.rerandomize == RANDOMIZATION.ALWAYS)

        # If the problem is closed (past due / too many attempts)
        # then we disable the "submit" button
        # Also, disable the "submit" button if we're waiting
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

        # If the problem is closed (and not a survey question with max_attempts==0),
        # then do NOT show the reset button.
        if self.closed() and not is_survey_question:
            return False

        # Button only shows up for randomized problems if the question has been submitted
        if self.rerandomize in [RANDOMIZATION.ALWAYS, RANDOMIZATION.ONRESET] and self.is_submitted():
            return True
        else:
            # Do NOT show the button if the problem is correct
            if self.is_correct():
                return False
            else:
                return self.show_reset_button

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
            needs_reset = self.is_submitted() and self.rerandomize == RANDOMIZATION.ALWAYS

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
            if self.max_attempts is None and self.rerandomize != RANDOMIZATION.ALWAYS:
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
        Create a dummy problem to represent any errors.

        Change our problem to a dummy problem containing a warning message to
        display to users. Returns the HTML to show to users

        `err` is the Exception encountered while rendering the problem HTML.
        """
        log.exception(err.message)

        # TODO (vshnayder): another switch on DEBUG.
        if self.runtime.DEBUG:
            msg = (
                u'[courseware.capa.capa_module] <font size="+1" color="red">'
                u'Failed to generate HTML for problem {url}</font>'.format(
                    url=cgi.escape(self.location.to_deprecated_string()))
            )
            msg += u'<p>Error:</p><p><pre>{msg}</pre></p>'.format(msg=cgi.escape(err.message))
            msg += u'<p><pre>{tb}</pre></p>'.format(tb=cgi.escape(traceback.format_exc()))
            html = msg

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

            # Next, generate a fresh LoncapaProblem
            self.lcp = self.new_lcp(None)
            self.set_state_from_lcp()

            # Prepend a scary warning to the student
            _ = self.runtime.service(self, "i18n").ugettext
            warning_msg = _("Warning: The problem has been reset to its initial state!")
            warning = '<div class="capa_reset"> <h2> ' + warning_msg + '</h2>'

            # Translators: Following this message, there will be a bulleted list of items.
            warning_msg = _("The problem's state was corrupted by an invalid submission. The submission consisted of:")
            warning += warning_msg + '<ul>'

            for student_answer in student_answers.values():
                if student_answer != '':
                    warning += '<li>' + cgi.escape(student_answer) + '</li>'

            warning_msg = _('If this error persists, please contact the course staff.')
            warning += '</ul>' + warning_msg + '</div>'

            html = warning
            try:
                html += self.lcp.get_html()
            except Exception:
                # Couldn't do it. Give up.
                log.exception("Unable to generate html from LoncapaProblem")
                raise

        return html

    def _should_enable_demand_hint(self, demand_hints, hint_index=None):
        """
        Should the demand hint option be enabled?

        Arguments:
            hint_index (int): The current hint index, or None (default value) if no hint is currently being shown.
            demand_hints (list): List of hints.
        Returns:
            bool: True is the demand hint is possible.
            bool: True is demand hint should be enabled.
        """
        # hint_index is the index of the last hint that will be displayed in this rendering,
        # so add 1 to check if others exist.
        if hint_index is None:
            should_enable = len(demand_hints) > 0
        else:
            should_enable = len(demand_hints) > 0 and hint_index + 1 < len(demand_hints)
        return len(demand_hints) > 0, should_enable

    def get_demand_hint(self, hint_index):
        """
        Return html for the problem, including demand hints.

        hint_index (int): (None is the default) if not None, this is the index of the next demand
            hint to show.
        """
        demand_hints = self.lcp.tree.xpath("//problem/demandhint/hint")
        hint_index = hint_index % len(demand_hints)

        _ = self.runtime.service(self, "i18n").ugettext

        counter = 0
        total_text = ''
        while counter <= hint_index:
            # Translators: {previous_hints} is the HTML of hints that have already been generated, {hint_number_prefix}
            # is a header for this hint, and {hint_text} is the text of the hint itself.
            # This string is being passed to translation only for possible reordering of the placeholders.
            total_text = HTML(_('{previous_hints}<li><strong>{hint_number_prefix}</strong>{hint_text}</li>')).format(
                previous_hints=HTML(total_text),
                # Translators: e.g. "Hint 1 of 3: " meaning we are showing the first of three hints.
                # This text is shown in bold before the accompanying hint text.
                hint_number_prefix=Text(_("Hint ({hint_num} of {hints_count}): ")).format(
                    hint_num=counter + 1, hints_count=len(demand_hints)
                ),
                # Course-authored HTML demand hints are supported.
                hint_text=HTML(get_inner_html_from_xpath(demand_hints[counter]))
            )
            counter += 1

        total_text = HTML('<ol>{hints}</ol>').format(hints=total_text)

        # Log this demand-hint request. Note that this only logs the last hint requested (although now
        # all previously shown hints are still displayed).
        event_info = dict()
        event_info['module_id'] = self.location.to_deprecated_string()
        event_info['hint_index'] = hint_index
        event_info['hint_len'] = len(demand_hints)
        event_info['hint_text'] = get_inner_html_from_xpath(demand_hints[hint_index])
        self.runtime.publish(self, 'edx.problem.hint.demandhint_displayed', event_info)

        _, should_enable_next_hint = self._should_enable_demand_hint(demand_hints=demand_hints, hint_index=hint_index)

        # We report the index of this hint, the client works out what index to use to get the next hint
        return {
            'success': True,
            'hint_index': hint_index,
            'should_enable_next_hint': should_enable_next_hint,
            'msg': total_text,
        }

    def get_problem_html(self, encapsulate=True, submit_notification=False):
        """
        Return html for the problem.

        Adds submit, reset, save, and hint buttons as necessary based on the problem config
        and state.

        encapsulate (bool): if True (the default) embed the html in a problem <div>
        submit_notification (bool): True if the submit notification should be added
        """
        try:
            html = self.lcp.get_html()

        # If we cannot construct the problem HTML,
        # then generate an error message instead.
        except Exception as err:  # pylint: disable=broad-except
            html = self.handle_problem_html_error(err)

        html = self.remove_tags_from_html(html)

        # Enable/Disable Submit button if should_enable_submit_button returns True/False.
        submit_button = self.submit_button_name()
        submit_button_submitting = self.submit_button_submitting_name()
        should_enable_submit_button = self.should_enable_submit_button()

        content = {
            'name': self.display_name_with_default,
            'html': html,
            'weight': self.weight,
        }

        # If demand hints are available, emit hint button and div.
        demand_hints = self.lcp.tree.xpath("//problem/demandhint/hint")
        demand_hint_possible, should_enable_next_hint = self._should_enable_demand_hint(demand_hints=demand_hints)

        answer_notification_type, answer_notification_message = self._get_answer_notification(
            render_notifications=submit_notification)

        context = {
            'problem': content,
            'id': self.location.to_deprecated_string(),
            'short_id': self.location.html_id(),
            'submit_button': submit_button,
            'submit_button_submitting': submit_button_submitting,
            'should_enable_submit_button': should_enable_submit_button,
            'reset_button': self.should_show_reset_button(),
            'save_button': self.should_show_save_button(),
            'answer_available': self.answer_available(),
            'attempts_used': self.attempts,
            'attempts_allowed': self.max_attempts,
            'demand_hint_possible': demand_hint_possible,
            'should_enable_next_hint': should_enable_next_hint,
            'answer_notification_type': answer_notification_type,
            'answer_notification_message': answer_notification_message,
        }

        html = self.runtime.render_template('problem.html', context)

        if encapsulate:
            html = u'<div id="problem_{id}" class="problem" data-url="{ajax_url}">'.format(
                id=self.location.html_id(), ajax_url=self.runtime.ajax_url
            ) + html + "</div>"

        # Now do all the substitutions which the LMS module_render normally does, but
        # we need to do here explicitly since we can get called for our HTML via AJAX
        html = self.runtime.replace_urls(html)
        if self.runtime.replace_course_urls:
            html = self.runtime.replace_course_urls(html)

        if self.runtime.replace_jump_to_id_urls:
            html = self.runtime.replace_jump_to_id_urls(html)

        return html

    def _get_answer_notification(self, render_notifications):
        """
        Generate the answer notification type and message from the current problem status.

         Arguments:
             render_notifications (bool): If false the method will return an None for type and message
        """
        answer_notification_message = None
        answer_notification_type = None

        if render_notifications:
            progress = self.get_progress()
            id_list = self.lcp.correct_map.keys()
            if len(id_list) == 1:
                # Only one answer available
                answer_notification_type = self.lcp.correct_map.get_correctness(id_list[0])
            elif len(id_list) > 1:
                # Check the multiple answers that are available
                answer_notification_type = self.lcp.correct_map.get_correctness(id_list[0])
                for answer_id in id_list[1:]:
                    if self.lcp.correct_map.get_correctness(answer_id) != answer_notification_type:
                        # There is at least 1 of the following combinations of correctness states
                        # Correct and incorrect, Correct and partially correct, or Incorrect and partially correct
                        # which all should have a message type of Partially Correct
                        answer_notification_type = 'partially-correct'
                        break

            # Build the notification message based on the notification type and translate it.
            ungettext = self.runtime.service(self, "i18n").ungettext
            if answer_notification_type == 'incorrect':
                if progress is not None:
                    answer_notification_message = ungettext(
                        "Incorrect ({progress} point)",
                        "Incorrect ({progress} points)",
                        progress.frac()[1]
                    ).format(progress=str(progress))
                else:
                    answer_notification_message = _('Incorrect')
            elif answer_notification_type == 'correct':
                if progress is not None:
                    answer_notification_message = ungettext(
                        "Correct ({progress} point)",
                        "Correct ({progress} points)",
                        progress.frac()[1]
                    ).format(progress=str(progress))
                else:
                    answer_notification_message = _('Correct')
            elif answer_notification_type == 'partially-correct':
                if progress is not None:
                    answer_notification_message = ungettext(
                        "Partially correct ({progress} point)",
                        "Partially correct ({progress} points)",
                        progress.frac()[1]
                    ).format(progress=str(progress))
                else:
                    answer_notification_message = _('Partially Correct')

        return answer_notification_type, answer_notification_message

    def remove_tags_from_html(self, html):
        """
        The capa xml includes many tags such as <additional_answer> or <demandhint> which are not
        meant to be part of the client html. We strip them all and return the resulting html.
        """
        tags = ['demandhint', 'choicehint', 'optionhint', 'stringhint', 'numerichint', 'optionhint',
                'correcthint', 'regexphint', 'additional_answer', 'stringequalhint', 'compoundhint',
                'stringequalhint']
        for tag in tags:
            html = re.sub(r'<%s.*?>.*?</%s>' % (tag, tag), '', html, flags=re.DOTALL)
            # Some of these tags span multiple lines
        # Note: could probably speed this up by calling sub() once with a big regex
        # vs. simply calling sub() many times as we have here.
        return html

    def hint_button(self, data):
        """
        Hint button handler, returns new html using hint_index from the client.
        """
        hint_index = int(data['hint_index'])
        return self.get_demand_hint(hint_index)

    def is_past_due(self):
        """
        Is it now past this problem's due date, including grace period?
        """
        return (self.close_date is not None and
                datetime.datetime.now(UTC()) > self.close_date)

    def closed(self):
        """
        Is the student still allowed to submit answers?
        """
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
        # used by conditional module
        return self.lcp.done

    def is_attempted(self):
        """
        Has the problem been attempted?

        used by conditional module
        """
        return self.attempts > 0

    def is_correct(self):
        """
        True iff full points
        """
        score_dict = self.get_score()
        return score_dict['score'] == score_dict['total']

    def answer_available(self):
        """
        Is the user allowed to see an answer?
        """
        if self.showanswer == '':
            return False
        elif self.showanswer == SHOWANSWER.NEVER:
            return False
        elif self.runtime.user_is_staff:
            # This is after the 'never' check because admins can see the answer
            # unless the problem explicitly prevents it
            return True
        elif self.showanswer == SHOWANSWER.ATTEMPTED:
            return self.attempts > 0
        elif self.showanswer == SHOWANSWER.ANSWERED:
            # NOTE: this is slightly different from 'attempted' -- resetting the problems
            # makes lcp.done False, but leaves attempts unchanged.
            return self.lcp.done
        elif self.showanswer == SHOWANSWER.CLOSED:
            return self.closed()
        elif self.showanswer == SHOWANSWER.FINISHED:
            return self.closed() or self.is_correct()

        elif self.showanswer == SHOWANSWER.CORRECT_OR_PAST_DUE:
            return self.is_correct() or self.is_past_due()
        elif self.showanswer == SHOWANSWER.PAST_DUE:
            return self.is_past_due()
        elif self.showanswer == SHOWANSWER.ALWAYS:
            return True

        return False

    def update_score(self, data):
        """
        Delivers grading response (e.g. from asynchronous code checking) to
            the capa problem, so its score can be updated

        'data' must have a key 'response' which is a string that contains the
            grader's response

        No ajax return is needed. Return empty dict.
        """
        queuekey = data['queuekey']
        score_msg = data['xqueue_body']
        self.lcp.update_score(score_msg, queuekey)
        self.set_state_from_lcp()
        self.publish_grade()

        return dict()  # No AJAX return is needed

    def handle_ungraded_response(self, data):
        """
        Delivers a response from the XQueue to the capa problem

        The score of the problem will not be updated

        Args:
            - data (dict) must contain keys:
                            queuekey - a key specific to this response
                            xqueue_body - the body of the response
        Returns:
            empty dictionary

        No ajax return is needed, so an empty dict is returned
        """
        queuekey = data['queuekey']
        score_msg = data['xqueue_body']

        # pass along the xqueue message to the problem
        self.lcp.ungraded_response(score_msg, queuekey)
        self.set_state_from_lcp()
        return dict()

    def handle_input_ajax(self, data):
        """
        Handle ajax calls meant for a particular input in the problem

        Args:
            - data (dict) - data that should be passed to the input
        Returns:
            - dict containing the response from the input
        """
        response = self.lcp.handle_input_ajax(data)

        # save any state changes that may occur
        self.set_state_from_lcp()
        return response

    def get_answer(self, _data):
        """
        For the "show answer" button.

        Returns the answers: {'answers' : answers}
        """
        event_info = dict()
        event_info['problem_id'] = self.location.to_deprecated_string()
        self.track_function_unmask('showanswer', event_info)
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
                answer_content = self.runtime.replace_urls(answers[answer_id])
                if self.runtime.replace_jump_to_id_urls:
                    answer_content = self.runtime.replace_jump_to_id_urls(answer_content)
                new_answer = {answer_id: answer_content}
            except TypeError:
                log.debug(u'Unable to perform URL substitution on answers[%s]: %s',
                          answer_id, answers[answer_id])
                new_answer = {answer_id: answers[answer_id]}
            new_answers.update(new_answer)

        return {'answers': new_answers}

    # Figure out if we should move these to capa_problem?
    def get_problem(self, _data):
        """
        Return results of get_problem_html, as a simple dict for json-ing.
        { 'html': <the-html> }

        Used if we want to reconfirm we have the right thing e.g. after
        several AJAX calls.
        """
        return {'html': self.get_problem_html(encapsulate=False, submit_notification=True)}

    @staticmethod
    def make_dict_of_responses(data):
        """
        Make dictionary of student responses (aka "answers")

        `data` is POST dictionary (webob.multidict.MultiDict).

        The `data` dict has keys of the form 'x_y', which are mapped
        to key 'y' in the returned dict.  For example,
        'input_1_2_3' would be mapped to '1_2_3' in the returned dict.

        Some inputs always expect a list in the returned dict
        (e.g. checkbox inputs).  The convention is that
        keys in the `data` dict that end with '[]' will always
        have list values in the returned dict.
        For example, if the `data` dict contains {'input_1[]': 'test' }
        then the output dict would contain {'1': ['test'] }
        (the value is a list).

        Some other inputs such as ChoiceTextInput expect a dict of values in the returned
        dict  If the key ends with '{}' then we will assume that the value is a json
        encoded dict and deserialize it.
        For example, if the `data` dict contains {'input_1{}': '{"1_2_1": 1}'}
        then the output dict would contain {'1': {"1_2_1": 1} }
        (the value is a dictionary)

        Raises an exception if:

        -A key in the `data` dictionary does not contain at least one underscore
          (e.g. "input" is invalid, but "input_1" is valid)

        -Two keys end up with the same name in the returned dict.
          (e.g. 'input_1' and 'input_1[]', which both get mapped to 'input_1'
           in the returned dict)
        """
        answers = dict()

        # webob.multidict.MultiDict is a view of a list of tuples,
        # so it will return a multi-value key once for each value.
        # We only want to consider each key a single time, so we use set(data.keys())
        for key in set(data.keys()):
            # e.g. input_resistor_1 ==> resistor_1
            _, _, name = key.partition('_')

            # If key has no underscores, then partition
            # will return (key, '', '')
            # We detect this and raise an error
            if not name:
                raise ValueError(u"{key} must contain at least one underscore".format(key=key))

            else:
                # This allows for answers which require more than one value for
                # the same form input (e.g. checkbox inputs). The convention is that
                # if the name ends with '[]' (which looks like an array), then the
                # answer will be an array.
                # if the name ends with '{}' (Which looks like a dict),
                # then the answer will be a dict
                is_list_key = name.endswith('[]')
                is_dict_key = name.endswith('{}')
                name = name[:-2] if is_list_key or is_dict_key else name

                if is_list_key:
                    val = data.getall(key)
                elif is_dict_key:
                    try:
                        val = json.loads(data[key])
                    # If the submission wasn't deserializable, raise an error.
                    except(KeyError, ValueError):
                        raise ValueError(
                            u"Invalid submission: {val} for {key}".format(val=data[key], key=key)
                        )
                else:
                    val = data[key]

                # If the name already exists, then we don't want
                # to override it.  Raise an error instead
                if name in answers:
                    raise ValueError(u"Key {name} already exists in answers dict".format(name=name))
                else:
                    answers[name] = val

        return answers

    def publish_grade(self):
        """
        Publishes the student's current grade to the system as an event
        """
        score = self.lcp.get_score()
        self.runtime.publish(
            self,
            'grade',
            {
                'value': score['score'],
                'max_value': score['total'],
            }
        )

        return {'grade': score['score'], 'max_grade': score['total']}

    # pylint: disable=too-many-statements
    def submit_problem(self, data, override_time=False):
        """
        Checks whether answers to a problem are correct

        Returns a map of correct/incorrect answers:
          {'success' : 'correct' | 'incorrect' | AJAX alert msg string,
           'contents' : html}
        """
        event_info = dict()
        event_info['state'] = self.lcp.get_state()
        event_info['problem_id'] = self.location.to_deprecated_string()

        answers = self.make_dict_of_responses(data)
        answers_without_files = convert_files_to_filenames(answers)
        event_info['answers'] = answers_without_files

        metric_name = u'capa.check_problem.{}'.format
        # Can override current time
        current_time = datetime.datetime.now(UTC())
        if override_time is not False:
            current_time = override_time

        _ = self.runtime.service(self, "i18n").ugettext

        # Too late. Cannot submit
        if self.closed():
            event_info['failure'] = 'closed'
            self.track_function_unmask('problem_check_fail', event_info)
            if dog_stats_api:
                dog_stats_api.increment(metric_name('checks'), tags=[u'result:failed', u'failure:closed'])
            raise NotFoundError(_("Problem is closed."))

        # Problem submitted. Student should reset before checking again
        if self.done and self.rerandomize == RANDOMIZATION.ALWAYS:
            event_info['failure'] = 'unreset'
            self.track_function_unmask('problem_check_fail', event_info)
            if dog_stats_api:
                dog_stats_api.increment(metric_name('checks'), tags=[u'result:failed', u'failure:unreset'])
            raise NotFoundError(_("Problem must be reset before it can be submitted again."))

        # Problem queued. Students must wait a specified waittime before they are allowed to submit
        # IDEA: consider stealing code from below: pretty-print of seconds, cueing of time remaining
        if self.lcp.is_queued():
            prev_submit_time = self.lcp.get_recentmost_queuetime()

            waittime_between_requests = self.runtime.xqueue['waittime']
            if (current_time - prev_submit_time).total_seconds() < waittime_between_requests:
                msg = _(u"You must wait at least {wait} seconds between submissions.").format(
                    wait=waittime_between_requests)
                return {'success': msg, 'html': ''}

        # Wait time between resets: check if is too soon for submission.
        if self.last_submission_time is not None and self.submission_wait_seconds != 0:
            if (current_time - self.last_submission_time).total_seconds() < self.submission_wait_seconds:
                remaining_secs = int(self.submission_wait_seconds - (current_time - self.last_submission_time).total_seconds())
                msg = _(u'You must wait at least {wait_secs} between submissions. {remaining_secs} remaining.').format(
                    wait_secs=self.pretty_print_seconds(self.submission_wait_seconds),
                    remaining_secs=self.pretty_print_seconds(remaining_secs))
                return {
                    'success': msg,
                    'html': ''
                }

        try:
            correct_map = self.lcp.grade_answers(answers)
            self.attempts = self.attempts + 1
            self.lcp.done = True
            self.set_state_from_lcp()
            self.set_last_submission_time()

        except (StudentInputError, ResponseError, LoncapaProblemError) as inst:
            if self.runtime.DEBUG:
                log.warning(
                    "StudentInputError in capa_module:problem_check",
                    exc_info=True
                )

            # Save the user's state before failing
            self.set_state_from_lcp()

            # If the user is a staff member, include
            # the full exception, including traceback,
            # in the response
            if self.runtime.user_is_staff:
                msg = u"Staff debug info: {tb}".format(tb=cgi.escape(traceback.format_exc()))

            # Otherwise, display just an error message,
            # without a stack trace
            else:
                # Translators: {msg} will be replaced with a problem's error message.
                msg = _(u"Error: {msg}").format(msg=inst.message)

            return {'success': msg}

        except Exception as err:
            # Save the user's state before failing
            self.set_state_from_lcp()

            if self.runtime.DEBUG:
                msg = u"Error checking problem: {}".format(err.message)
                msg += u'\nTraceback:\n{}'.format(traceback.format_exc())
                return {'success': msg}
            raise

        published_grade = self.publish_grade()

        # success = correct if ALL questions in this problem are correct
        success = 'correct'
        for answer_id in correct_map:
            if not correct_map.is_correct(answer_id):
                success = 'incorrect'

        # NOTE: We are logging both full grading and queued-grading submissions. In the latter,
        #       'success' will always be incorrect
        event_info['grade'] = published_grade['grade']
        event_info['max_grade'] = published_grade['max_grade']
        event_info['correct_map'] = correct_map.get_dict()
        event_info['success'] = success
        event_info['attempts'] = self.attempts
        event_info['submission'] = self.get_submission_metadata_safe(answers_without_files, correct_map)
        self.track_function_unmask('problem_check', event_info)

        if dog_stats_api:
            dog_stats_api.increment(metric_name('checks'), tags=[u'result:success'])
            if published_grade['max_grade'] != 0:
                dog_stats_api.histogram(
                    metric_name('correct_pct'),
                    float(published_grade['grade']) / published_grade['max_grade'],
                )
            dog_stats_api.histogram(
                metric_name('attempts'),
                self.attempts,
            )

        # render problem into HTML
        html = self.get_problem_html(encapsulate=False, submit_notification=True)

        return {
            'success': success,
            'contents': html
        }
    # pylint: enable=too-many-statements

    def track_function_unmask(self, title, event_info):
        """
        All calls to runtime.track_function route through here so that the
        choice names can be unmasked.
        """
        # Do the unmask translates on a copy of event_info,
        # avoiding problems where an event_info is unmasked twice.
        event_unmasked = copy.deepcopy(event_info)
        self.unmask_event(event_unmasked)
        self.runtime.publish(self, title, event_unmasked)

    def unmask_event(self, event_info):
        """
        Translates in-place the event_info to account for masking
        and adds information about permutation options in force.
        """
        # answers is like: {u'i4x-Stanford-CS99-problem-dada976e76f34c24bc8415039dee1300_2_1': u'mask_0'}
        # Each response values has an answer_id which matches the key in answers.
        for response in self.lcp.responders.values():
            # Un-mask choice names in event_info for masked responses.
            if response.has_mask():
                # We don't assume much about the structure of event_info,
                # but check for the existence of the things we need to un-mask.

                # Look for answers/id
                answer = event_info.get('answers', {}).get(response.answer_id)
                if answer is not None:
                    event_info['answers'][response.answer_id] = response.unmask_name(answer)

                # Look for state/student_answers/id
                answer = event_info.get('state', {}).get('student_answers', {}).get(response.answer_id)
                if answer is not None:
                    event_info['state']['student_answers'][response.answer_id] = response.unmask_name(answer)

                # Look for old_state/student_answers/id  -- parallel to the above case, happens on reset
                answer = event_info.get('old_state', {}).get('student_answers', {}).get(response.answer_id)
                if answer is not None:
                    event_info['old_state']['student_answers'][response.answer_id] = response.unmask_name(answer)

            # Add 'permutation' to event_info for permuted responses.
            permutation_option = None
            if response.has_shuffle():
                permutation_option = 'shuffle'
            elif response.has_answerpool():
                permutation_option = 'answerpool'

            if permutation_option is not None:
                # Add permutation record tuple: (one of:'shuffle'/'answerpool', [as-displayed list])
                if 'permutation' not in event_info:
                    event_info['permutation'] = {}
                event_info['permutation'][response.answer_id] = (permutation_option, response.unmask_order())

    def pretty_print_seconds(self, num_seconds):
        """
        Returns time duration nicely formated, e.g. "3 minutes 4 seconds"
        """
        # Here _ is the N variant ungettext that does pluralization with a 3-arg call
        ungettext = self.runtime.service(self, "i18n").ungettext
        hours = num_seconds // 3600
        sub_hour = num_seconds % 3600
        minutes = sub_hour // 60
        seconds = sub_hour % 60
        display = ""
        if hours > 0:
            display += ungettext("{num_hour} hour", "{num_hour} hours", hours).format(num_hour=hours)
        if minutes > 0:
            if display != "":
                display += " "
            # translators: "minute" refers to a minute of time
            display += ungettext("{num_minute} minute", "{num_minute} minutes", minutes).format(num_minute=minutes)
        # Taking care to make "0 seconds" instead of "" for 0 time
        if seconds > 0 or (hours == 0 and minutes == 0):
            if display != "":
                display += " "
            # translators: "second" refers to a second of time
            display += ungettext("{num_second} second", "{num_second} seconds", seconds).format(num_second=seconds)
        return display

    def get_submission_metadata_safe(self, answers, correct_map):
        """
        Ensures that no exceptions are thrown while generating input metadata summaries.  Returns the
        summary if it is successfully created, otherwise an empty dictionary.
        """
        try:
            return self.get_submission_metadata(answers, correct_map)
        except Exception:  # pylint: disable=broad-except
            # NOTE: The above process requires deep inspection of capa structures that may break for some
            # uncommon problem types.  Ensure that it does not prevent answer submission in those
            # cases.  Any occurrences of errors in this block should be investigated and resolved.
            log.exception('Unable to gather submission metadata, it will not be included in the event.')

        return {}

    def get_submission_metadata(self, answers, correct_map):
        """
        Return a map of inputs to their corresponding summarized metadata.

        Returns:
            A map whose keys are a unique identifier for the input (in this case a capa input_id) and
            whose values are:

                question (str): Is the prompt that was presented to the student.  It corresponds to the
                    label of the input.
                answer (mixed): Is the answer the student provided.  This may be a rich structure,
                    however it must be json serializable.
                response_type (str): The XML tag of the capa response type.
                input_type (str): The XML tag of the capa input type.
                correct (bool): Whether or not the provided answer is correct.  Will be an empty
                    string if correctness could not be determined.
                variant (str): In some cases the same question can have several different variants.
                    This string should uniquely identify the variant of the question that was answered.
                    In the capa context this corresponds to the `seed`.

        This function attempts to be very conservative and make very few assumptions about the structure
        of the problem.  If problem related metadata cannot be located it should be replaced with empty
        strings ''.
        """
        input_metadata = {}
        for input_id, internal_answer in answers.iteritems():
            answer_input = self.lcp.inputs.get(input_id)

            if answer_input is None:
                log.warning('Input id %s is not mapped to an input type.', input_id)

            answer_response = None
            for response, responder in self.lcp.responders.iteritems():
                if input_id in responder.answer_ids:
                    answer_response = responder

            if answer_response is None:
                log.warning('Answer responder could not be found for input_id %s.', input_id)

            user_visible_answer = internal_answer
            if hasattr(answer_input, 'get_user_visible_answer'):
                user_visible_answer = answer_input.get_user_visible_answer(internal_answer)

            # If this problem has rerandomize enabled, then it will generate N variants of the
            # question, one per unique seed value.  In this case we would like to know which
            # variant was selected.  Ideally it would be nice to have the exact question that
            # was presented to the user, with values interpolated etc, but that can be done
            # later if necessary.
            variant = ''
            if self.rerandomize != RANDOMIZATION.NEVER:
                variant = self.seed

            is_correct = correct_map.is_correct(input_id)
            if is_correct is None:
                is_correct = ''

            response_data = getattr(answer_input, 'response_data', {})
            input_metadata[input_id] = {
                'question': response_data.get('label', ''),
                'answer': user_visible_answer,
                'response_type': getattr(getattr(answer_response, 'xml', None), 'tag', ''),
                'input_type': getattr(answer_input, 'tag', ''),
                'correct': is_correct,
                'variant': variant,
                'group_label': response_data.get('group_label', ''),
            }

        return input_metadata

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
        event_info = {'state': self.lcp.get_state(), 'problem_id': self.location.to_deprecated_string()}

        _ = self.runtime.service(self, "i18n").ugettext

        if not self.lcp.supports_rescoring():
            event_info['failure'] = 'unsupported'
            self.track_function_unmask('problem_rescore_fail', event_info)
            # Translators: 'rescoring' refers to the act of re-submitting a student's solution so it can get a new score.
            raise NotImplementedError(_("Problem's definition does not support rescoring."))

        if not self.done:
            event_info['failure'] = 'unanswered'
            self.track_function_unmask('problem_rescore_fail', event_info)
            raise NotFoundError(_("Problem must be answered before it can be graded again."))

        # get old score, for comparison:
        orig_score = self.lcp.get_score()
        event_info['orig_score'] = orig_score['score']
        event_info['orig_total'] = orig_score['total']

        try:
            correct_map = self.lcp.rescore_existing_answers()

        except (StudentInputError, ResponseError, LoncapaProblemError) as inst:
            log.warning("Input error in capa_module:problem_rescore", exc_info=True)
            event_info['failure'] = 'input_error'
            self.track_function_unmask('problem_rescore_fail', event_info)
            return {'success': u"Error: {0}".format(inst.message)}

        except Exception as err:
            event_info['failure'] = 'unexpected'
            self.track_function_unmask('problem_rescore_fail', event_info)
            if self.runtime.DEBUG:
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
        self.track_function_unmask('problem_rescore', event_info)

        return {'success': success}

    def save_problem(self, data):
        """
        Save the passed in answers.
        Returns a dict { 'success' : bool, 'msg' : message }
        The message is informative on success, and an error message on failure.
        """
        event_info = dict()
        event_info['state'] = self.lcp.get_state()
        event_info['problem_id'] = self.location.to_deprecated_string()

        answers = self.make_dict_of_responses(data)
        event_info['answers'] = answers
        _ = self.runtime.service(self, "i18n").ugettext

        # Too late. Cannot submit
        if self.closed() and not self.max_attempts == 0:
            event_info['failure'] = 'closed'
            self.track_function_unmask('save_problem_fail', event_info)
            return {
                'success': False,
                # Translators: 'closed' means the problem's due date has passed. You may no longer attempt to solve the problem.
                'msg': _("Problem is closed.")
            }

        # Problem submitted. Student should reset before saving
        # again.
        if self.done and self.rerandomize == RANDOMIZATION.ALWAYS:
            event_info['failure'] = 'done'
            self.track_function_unmask('save_problem_fail', event_info)
            return {
                'success': False,
                'msg': _("Problem needs to be reset prior to save.")
            }

        self.lcp.student_answers = answers

        self.set_state_from_lcp()

        self.track_function_unmask('save_problem_success', event_info)
        msg = _("Your answers have been saved.")
        if not self.max_attempts == 0:
            msg = _(
                "Your answers have been saved but not graded. Click '{button_name}' to grade them."
            ).format(button_name=self.submit_button_name())
        return {
            'success': True,
            'msg': msg,
            'html': self.get_problem_html(encapsulate=False)
        }

    def reset_problem(self, _data):
        """
        Changes problem state to unfinished -- removes student answers,
        Causes problem to rerender itself if randomization is enabled.

        Returns a dictionary of the form:
          {'success': True/False,
           'html': Problem HTML string }

        If an error occurs, the dictionary will also have an
        `error` key containing an error message.
        """
        event_info = dict()
        event_info['old_state'] = self.lcp.get_state()
        event_info['problem_id'] = self.location.to_deprecated_string()
        _ = self.runtime.service(self, "i18n").ugettext

        if self.closed():
            event_info['failure'] = 'closed'
            self.track_function_unmask('reset_problem_fail', event_info)
            return {
                'success': False,
                # Translators: 'closed' means the problem's due date has passed. You may no longer attempt to solve the problem.
                'msg': _("You cannot select Reset for a problem that is closed."),
            }

        if not self.is_submitted():
            event_info['failure'] = 'not_done'
            self.track_function_unmask('reset_problem_fail', event_info)
            return {
                'success': False,
                'msg': _("You must submit an answer before you can select Reset."),
            }

        if self.is_submitted() and self.rerandomize in [RANDOMIZATION.ALWAYS, RANDOMIZATION.ONRESET]:
            # Reset random number generator seed.
            self.choose_new_seed()

        # Generate a new problem with either the previous seed or a new seed
        self.lcp = self.new_lcp(None)

        # Pull in the new problem seed
        self.set_state_from_lcp()

        # Grade may have changed, so publish new value
        self.publish_grade()

        event_info['new_state'] = self.lcp.get_state()
        self.track_function_unmask('reset_problem', event_info)

        return {
            'success': True,
            'html': self.get_problem_html(encapsulate=False),
        }
