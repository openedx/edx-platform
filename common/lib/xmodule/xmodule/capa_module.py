import cgi
import datetime
import dateutil
import dateutil.parser
import json
import logging
import traceback
import re
import sys

from datetime import timedelta
from lxml import etree
from pkg_resources import resource_string

from capa.capa_problem import LoncapaProblem
from capa.responsetypes import StudentInputError
from capa.util import convert_files_to_filenames
from progress import Progress
from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.exceptions import NotFoundError

log = logging.getLogger("mitx.courseware")

#-----------------------------------------------------------------------------
TIMEDELTA_REGEX = re.compile(r'^((?P<days>\d+?) day(?:s?))?(\s)?((?P<hours>\d+?) hour(?:s?))?(\s)?((?P<minutes>\d+?) minute(?:s)?)?(\s)?((?P<seconds>\d+?) second(?:s)?)?$')


def only_one(lst, default="", process=lambda x: x):
    """
    If lst is empty, returns default
    If lst has a single element, applies process to that element and returns it
    Otherwise, raises an exeception
    """
    if len(lst) == 0:
        return default
    elif len(lst) == 1:
        return process(lst[0])
    else:
        raise Exception('Malformed XML')


def parse_timedelta(time_str):
    """
    time_str: A string with the following components:
        <D> day[s] (optional)
        <H> hour[s] (optional)
        <M> minute[s] (optional)
        <S> second[s] (optional)

    Returns a datetime.timedelta parsed from the string
    """
    parts = TIMEDELTA_REGEX.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.iteritems():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, complex):
            return "{real:.7g}{imag:+.7g}*j".format(real=obj.real, imag=obj.imag)
        return json.JSONEncoder.default(self, obj)


class CapaModule(XModule):
    '''
    An XModule implementing LonCapa format problems, implemented by way of
    capa.capa_problem.LoncapaProblem
    '''
    icon_class = 'problem'

    js = {'coffee': [resource_string(__name__, 'js/src/capa/display.coffee')],
          'js': [resource_string(__name__, 'js/src/capa/imageinput.js'),
                 resource_string(__name__, 'js/src/capa/schematic.js')]}
    js_module_name = "Problem"
    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}

    def __init__(self, system, location, definition, descriptor, instance_state=None,
                 shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor, instance_state,
                         shared_state, **kwargs)

        self.attempts = 0
        self.max_attempts = None

        dom2 = etree.fromstring(definition['data'])

        display_due_date_string = self.metadata.get('due', None)
        if display_due_date_string is not None:
            self.display_due_date = dateutil.parser.parse(display_due_date_string)
            #log.debug("Parsed " + display_due_date_string +
            #          " to " + str(self.display_due_date))
        else:
            self.display_due_date = None

        grace_period_string = self.metadata.get('graceperiod', None)
        if grace_period_string is not None and self.display_due_date:
            self.grace_period = parse_timedelta(grace_period_string)
            self.close_date = self.display_due_date + self.grace_period
            #log.debug("Then parsed " + grace_period_string +
            #          " to closing date" + str(self.close_date))
        else:
            self.grace_period = None
            self.close_date = self.display_due_date

        self.max_attempts = self.metadata.get('attempts', None)
        if self.max_attempts is not None:
            self.max_attempts = int(self.max_attempts)

        self.show_answer = self.metadata.get('showanswer', 'closed')

        if self.show_answer == "":
            self.show_answer = "closed"

        if instance_state is not None:
            instance_state = json.loads(instance_state)
        if instance_state is not None and 'attempts' in instance_state:
            self.attempts = instance_state['attempts']

        self.name = only_one(dom2.xpath('/problem/@name'))

        weight_string = only_one(dom2.xpath('/problem/@weight'))
        if weight_string:
            self.weight = float(weight_string)
        else:
            self.weight = None

        if self.rerandomize == 'never':
            self.seed = 1
        elif self.rerandomize == "per_student" and hasattr(self.system, 'id'):
            self.seed = system.id
        else:
            self.seed = None

        try:
            # TODO (vshnayder): move as much as possible of this work and error
            # checking to descriptor load time
            self.lcp = LoncapaProblem(self.definition['data'], self.location.html_id(),
                                      instance_state, seed=self.seed, system=self.system)
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
                self.lcp = LoncapaProblem(
                    problem_text, self.location.html_id(),
                    instance_state, seed=self.seed, system=self.system)
            else:
                # add extra info and raise
                raise Exception(msg), None, sys.exc_info()[2]

    @property
    def rerandomize(self):
        """
        Property accessor that returns self.metadata['rerandomize'] in a
        canonical form
        """
        rerandomize = self.metadata.get('rerandomize', 'always')
        if rerandomize in ("", "always", "true"):
            return "always"
        elif rerandomize in ("false", "per_student"):
            return "per_student"
        elif rerandomize == "never":
            return "never"
        else:
            raise Exception("Invalid rerandomize attribute " + rerandomize)

    def get_instance_state(self):
        state = self.lcp.get_state()
        state['attempts'] = self.attempts
        return json.dumps(state)

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
            except Exception as err:
                log.exception("Got bad progress")
                return None
        return None

    def get_html(self):
        return self.system.render_template('problem_ajax.html', {
            'element_id': self.location.html_id(),
            'id': self.id,
            'ajax_url': self.system.ajax_url,
        })

    def get_problem_html(self, encapsulate=True):
        '''Return html for the problem.  Adds check, reset, save buttons
        as necessary based on the problem config and state.'''

        try:
            html = self.lcp.get_html()
        except Exception, err:
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
                self.lcp = LoncapaProblem(self.definition['data'], self.location.html_id(),
                               state=None, # Tabula rasa
                               seed=self.seed, system=self.system)

                # Prepend a scary warning to the student
                warning  = '<div class="capa_reset">'
                warning += '<h2>Problem reset to initial state!</h2>'
                warning += '<p>Problem state was corruped by invalid submission. The submission consisted of:</p>'
                warning += '<ul>'
                for student_answer in student_answers.values():
                    if student_answer != '':
                        warning += '<li>' + cgi.escape(student_answer) + '</li>'
                warning += '</ul>'
                warning += '<p>If problem persists, please contact the course staff.</p>'
                warning += '</div>'

                html = warning
                try:
                    html += self.lcp.get_html()
                except Exception, err: # Couldn't do it. Give up
                    log.exception(err)
                    raise

        content = {'name': self.display_name,
                   'html': html,
                   'weight': self.weight,
                   }

        # We using strings as truthy values, because the terminology of the
        # check button is context-specific.

        # Put a "Check" button if unlimited attempts or still some left
        if self.max_attempts is None or self.attempts < self.max_attempts-1: 
            check_button = "Check"
        else:
            # Will be final check so let user know that
            check_button = "Final Check" 

        reset_button = True
        save_button = True

        # If we're after deadline, or user has exhausted attempts,
        # question is read-only.
        if self.closed():
            check_button = False
            reset_button = False
            save_button = False

        # User submitted a problem, and hasn't reset. We don't want
        # more submissions.
        if self.lcp.done and self.rerandomize == "always":
            check_button = False
            save_button = False

        # Only show the reset button if pressing it will show different values
        if self.rerandomize != 'always':
            reset_button = False

        # User hasn't submitted an answer yet -- we don't want resets
        if not self.lcp.done:
            reset_button = False

        # We don't need a "save" button if infinite number of attempts and
        # non-randomized
        if self.max_attempts is None and self.rerandomize != "always":
            save_button = False

        context = {'problem': content,
                   'id': self.id,
                   'check_button': check_button,
                   'reset_button': reset_button,
                   'save_button': save_button,
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

        return self.system.replace_urls(html, self.metadata['data_dir'])

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

    def closed(self):
        ''' Is the student still allowed to submit answers? '''
        if self.attempts == self.max_attempts:
            return True
        if self.close_date is not None and datetime.datetime.utcnow() > self.close_date:
            return True

        return False

    def answer_available(self):
        ''' Is the user allowed to see an answer?
        '''
        if self.show_answer == '':
            return False

        if self.show_answer == "never":
            return False

        # Admins can see the answer, unless the problem explicitly prevents it
        if self.system.user_is_staff:
            return True

        if self.show_answer == 'attempted':
            return self.attempts > 0

        if self.show_answer == 'answered':
            return self.lcp.done

        if self.show_answer == 'closed':
            return self.closed()

        if self.show_answer == 'always':
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

        return dict()  # No AJAX return is needed

    def get_answer(self, get):
        '''
        For the "show answer" button.

        Returns the answers: {'answers' : answers}
        '''
        event_info = dict()
        event_info['problem_id'] = self.location.url()
        self.system.track_function('show_answer', event_info)
        if not self.answer_available():
            raise NotFoundError('Answer is not available')
        else:
            answers = self.lcp.get_question_answers()

	    # answers (eg <solution>) may have embedded images
        #   but be careful, some problems are using non-string answer dicts
        new_answers = dict()
        for answer_id in answers:
            try:
                new_answer = {answer_id: self.system.replace_urls(answers[answer_id], self.metadata['data_dir'])}
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
        get is POST dictionary.
        '''
        answers = dict()
        for key in get:
            # e.g. input_resistor_1 ==> resistor_1
            _, _, name = key.partition('_')

            # This allows for answers which require more than one value for
            # the same form input (e.g. checkbox inputs). The convention is that
            # if the name ends with '[]' (which looks like an array), then the
            # answer will be an array.
            if not name.endswith('[]'):
                answers[name] = get[key]
            else:
                name = name[:-2]
                answers[name] = get.getlist(key)

        return answers

    def check_problem(self, get):
        ''' Checks whether answers to a problem are correct, and
            returns a map of correct/incorrect answers:

            {'success' : bool,
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
            self.system.track_function('save_problem_check_fail', event_info)
            raise NotFoundError('Problem is closed')

        # Problem submitted. Student should reset before checking again
        if self.lcp.done and self.rerandomize == "always":
            event_info['failure'] = 'unreset'
            self.system.track_function('save_problem_check_fail', event_info)
            raise NotFoundError('Problem must be reset before it can be checked again')

        # Problem queued. Students must wait a specified waittime before they are allowed to submit
        if self.lcp.is_queued():
            current_time = datetime.datetime.now()
            prev_submit_time = self.lcp.get_recentmost_queuetime() 
            waittime_between_requests = self.system.xqueue['waittime']
            if (current_time-prev_submit_time).total_seconds() < waittime_between_requests:
                msg = 'You must wait at least %d seconds between submissions' % waittime_between_requests
                return {'success': msg, 'html': ''} # Prompts a modal dialog in ajax callback 

        try:
            old_state = self.lcp.get_state()
            lcp_id = self.lcp.problem_id
            correct_map = self.lcp.grade_answers(answers)
        except StudentInputError as inst:
            # TODO (vshnayder): why is this line here?
            #self.lcp = LoncapaProblem(self.definition['data'],
            #                          id=lcp_id, state=old_state, system=self.system)
            log.exception("StudentInputError in capa_module:problem_check")
            return {'success': inst.message}
        except Exception, err:
            # TODO: why is this line here?
            #self.lcp = LoncapaProblem(self.definition['data'],
            #                          id=lcp_id, state=old_state, system=self.system)
            if self.system.DEBUG:
                msg = "Error checking problem: " + str(err)
                msg += '\nTraceback:\n' + traceback.format_exc()
                return {'success': msg}
            log.exception("Error in capa_module problem checking")
            raise Exception("error in capa_module")

        self.attempts = self.attempts + 1
        self.lcp.done = True

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
        self.system.track_function('save_problem_check', event_info)

	if hasattr(self.system,'psychometrics_handler'):	# update PsychometricsData using callback
		self.system.psychometrics_handler(self.get_instance_state())

        # render problem into HTML
        html = self.get_problem_html(encapsulate=False)

        return {'success': success,
                'contents': html,
                }

    def save_problem(self, get):
        '''
        Save the passed in answers.
        Returns a dict { 'success' : bool, ['error' : error-msg]},
        with the error key only present if success is False.
        '''
        event_info = dict()
        event_info['state'] = self.lcp.get_state()
        event_info['problem_id'] = self.location.url()

        answers = self.make_dict_of_responses(get)
        event_info['answers'] = answers

        # Too late. Cannot submit
        if self.closed():
            event_info['failure'] = 'closed'
            self.system.track_function('save_problem_fail', event_info)
            return {'success': False,
                    'error': "Problem is closed"}

        # Problem submitted. Student should reset before saving
        # again.
        if self.lcp.done and self.rerandomize == "always":
            event_info['failure'] = 'done'
            self.system.track_function('save_problem_fail', event_info)
            return {'success': False,
                    'error': "Problem needs to be reset prior to save."}

        self.lcp.student_answers = answers

        # TODO: should this be save_problem_fail?  Looks like success to me...
        self.system.track_function('save_problem_fail', event_info)
        return {'success': True}

    def reset_problem(self, get):
        ''' Changes problem state to unfinished -- removes student answers,
            and causes problem to rerender itself.

            Returns problem html as { 'html' : html-string }.
        '''
        event_info = dict()
        event_info['old_state'] = self.lcp.get_state()
        event_info['problem_id'] = self.location.url()

        if self.closed():
            event_info['failure'] = 'closed'
            self.system.track_function('reset_problem_fail', event_info)
            return "Problem is closed"

        if not self.lcp.done:
            event_info['failure'] = 'not_done'
            self.system.track_function('reset_problem_fail', event_info)
            return "Refresh the page and make an attempt before resetting."

        self.lcp.do_reset()
        if self.rerandomize == "always":
            # reset random number generator seed (note the self.lcp.get_state()
            # in next line)
            self.lcp.seed = None

        self.lcp = LoncapaProblem(self.definition['data'],
                                  self.location.html_id(), self.lcp.get_state(),
                                  system=self.system)

        event_info['new_state'] = self.lcp.get_state()
        self.system.track_function('reset_problem', event_info)

        return {'html': self.get_problem_html(encapsulate=False)}


class CapaDescriptor(RawDescriptor):
    """
    Module implementing problems in the LON-CAPA format,
    as implemented by capa.capa_problem
    """

    module_class = CapaModule

    stores_state = True
    has_score = True

    # Capa modules have some additional metadata:
    # TODO (vshnayder): do problems have any other metadata?  Do they
    # actually use type and points?
    metadata_attributes = RawDescriptor.metadata_attributes + ('type', 'points')

    # VS[compat]
    # TODO (cpennington): Delete this method once all fall 2012 course are being
    # edited in the cms
    @classmethod
    def backcompat_paths(cls, path):
        return [
            'problems/' + path[8:],
            path[8:],
        ]
