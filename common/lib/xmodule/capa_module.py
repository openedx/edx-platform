import datetime
import dateutil
import dateutil.parser
import json
import logging
import traceback
import re
import StringIO

from datetime import timedelta
from lxml import etree

from x_module import XModule, XModuleDescriptor
from progress import Progress
from capa.capa_problem import LoncapaProblem
from capa.responsetypes import StudentInputError

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


class ModuleDescriptor(XModuleDescriptor):
    pass


class Module(XModule):
    ''' Interface between capa_problem and x_module. Originally a hack
    meant to be refactored out, but it seems to be serving a useful
    prupose now. We can e.g .destroy and create the capa_problem on a
    reset.
    '''

    id_attribute = "filename"

    @classmethod
    def get_xml_tags(c):
        return ["problem"]


    def get_state(self):
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
            return Progress(score, total)
        return None


    def get_html(self):
        return self.system.render_template('problem_ajax.html', {
            'id': self.item_id,
            'ajax_url': self.ajax_url,
        })


    def get_problem_html(self, encapsulate=True):
        '''Return html for the problem.  Adds check, reset, save buttons
        as necessary based on the problem config and state.'''

        try:
            html = self.lcp.get_html()
        except Exception, err:
            if self.DEBUG:
                log.exception(err)
                msg = '[courseware.capa.capa_module] <font size="+1" color="red">Failed to generate HTML for problem %s</font>' % (self.filename)
                msg += '<p>Error:</p><p><pre>%s</pre></p>' % str(err).replace('<','&lt;')
                msg += '<p><pre>%s</pre></p>' % traceback.format_exc().replace('<','&lt;')
                html = msg
            else:
                raise
                
        content = {'name': self.name,
                   'html': html,
                   'weight': self.weight,
                  }

        # We using strings as truthy values, because the terminology of the check button
        # is context-specific.
        check_button = "Grade" if self.max_attempts else "Check"
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

        # We don't need a "save" button if infinite number of attempts and non-randomized
        if self.max_attempts is None and self.rerandomize != "always":
            save_button = False

        # Check if explanation is available, and if so, give a link
        explain = ""
        if self.lcp.done and self.explain_available == 'attempted':
            explain = self.explanation
        if self.closed() and self.explain_available == 'closed':
            explain = self.explanation

        if len(explain) == 0:
            explain = False

        context = {'problem': content,
                   'id': self.item_id,
                   'check_button': check_button,
                   'reset_button': reset_button,
                   'save_button': save_button,
                   'answer_available': self.answer_available(),
                   'ajax_url': self.ajax_url,
                   'attempts_used': self.attempts,
                   'attempts_allowed': self.max_attempts,
                   'explain': explain,
                   'progress': self.get_progress(),
                   }

        html = self.system.render_template('problem.html', context)
        if encapsulate:
            html = '<div id="problem_{id}" class="problem" data-url="{ajax_url}">'.format(
                id=self.item_id, ajax_url=self.ajax_url) + html + "</div>"

        return html

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)

        self.attempts = 0
        self.max_attempts = None

        dom2 = etree.fromstring(xml)

        self.explanation = "problems/" + only_one(dom2.xpath('/problem/@explain'),
                                                  default="closed")
        # TODO: Should be converted to: self.explanation=only_one(dom2.xpath('/problem/@explain'), default="closed")
        self.explain_available = only_one(dom2.xpath('/problem/@explain_available'))

        display_due_date_string = only_one(dom2.xpath('/problem/@due'))
        if len(display_due_date_string) > 0:
            self.display_due_date = dateutil.parser.parse(display_due_date_string)
            #log.debug("Parsed " + display_due_date_string + " to " + str(self.display_due_date))
        else:
            self.display_due_date = None

        grace_period_string = only_one(dom2.xpath('/problem/@graceperiod'))
        if len(grace_period_string) >0 and self.display_due_date:
            self.grace_period = parse_timedelta(grace_period_string)
            self.close_date = self.display_due_date + self.grace_period
            #log.debug("Then parsed " + grace_period_string + " to closing date" + str(self.close_date))
        else:
            self.grace_period = None
            self.close_date = self.display_due_date

        self.max_attempts = only_one(dom2.xpath('/problem/@attempts'))
        if len(self.max_attempts) > 0:
            self.max_attempts = int(self.max_attempts)
        else:
            self.max_attempts = None

        self.show_answer = only_one(dom2.xpath('/problem/@showanswer'))

        if self.show_answer == "":
            self.show_answer = "closed"

        self.rerandomize = only_one(dom2.xpath('/problem/@rerandomize'))
        if self.rerandomize == "" or self.rerandomize=="always" or self.rerandomize=="true":
            self.rerandomize="always"
        elif self.rerandomize=="false" or self.rerandomize=="per_student":
            self.rerandomize="per_student"
        elif self.rerandomize=="never":
            self.rerandomize="never"
        else:
            raise Exception("Invalid rerandomize attribute "+self.rerandomize)

        if state!=None:
            state=json.loads(state)
        if state!=None and 'attempts' in state:
            self.attempts=state['attempts']

        # TODO: Should be: self.filename=only_one(dom2.xpath('/problem/@filename'))
        self.filename= "problems/"+only_one(dom2.xpath('/problem/@filename'))+".xml"
        self.name=only_one(dom2.xpath('/problem/@name'))
        self.weight=only_one(dom2.xpath('/problem/@weight'))
        if self.rerandomize == 'never':
            seed = 1
        elif self.rerandomize == "per_student" and hasattr(system, 'id'):
            seed = system.id
        else:
            seed = None
        try:
            fp = self.filestore.open(self.filename)
        except Exception,err:
            log.exception('[courseware.capa.capa_module.Module.init] error %s: cannot open file %s' % (err,self.filename))
            if self.DEBUG:
                # create a dummy problem instead of failing
                fp = StringIO.StringIO('<problem><text><font color="red" size="+2">Problem file %s is missing</font></text></problem>' % self.filename)
                fp.name = "StringIO"
            else:
                raise
        try:
            self.lcp=LoncapaProblem(fp, self.item_id, state, seed = seed, system=self.system)
        except Exception,err:
            msg = '[courseware.capa.capa_module.Module.init] error %s: cannot create LoncapaProblem %s' % (err,self.filename)
            log.exception(msg)
            if self.DEBUG:
                msg = '<p>%s</p>' % msg.replace('<','&lt;')
                msg += '<p><pre>%s</pre></p>' % traceback.format_exc().replace('<','&lt;')
                # create a dummy problem with error message instead of failing
                fp = StringIO.StringIO('<problem><text><font color="red" size="+2">Problem file %s has an error:</font>%s</text></problem>' % (self.filename,msg))
                fp.name = "StringIO"
                self.lcp=LoncapaProblem(fp, self.item_id, state, seed = seed, system=self.system)
            else:
                raise

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
            }

        if dispatch not in handlers:
            return 'Error'

        before = self.get_progress()
        d = handlers[dispatch](get)
        after = self.get_progress()
        d.update({
            'progress_changed' : after != before,
            'progress_status' : Progress.to_js_status_str(after),
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

        if self.show_answer == 'attempted':
            return self.attempts > 0

        if self.show_answer == 'answered':
            return self.lcp.done

        if self.show_answer == 'closed':
            return self.closed()

        if self.show_answer == 'always':
            return True
        raise self.system.exception404 #TODO: Not 404

    def get_answer(self, get):
        '''
        For the "show answer" button.

        TODO: show answer events should be logged here, not just in the problem.js

        Returns the answers: {'answers' : answers}
        '''
        if not self.answer_available():
            raise self.system.exception404
        else:
            answers = self.lcp.get_question_answers()
            return {'answers' : answers}


    # Figure out if we should move these to capa_problem?
    def get_problem(self, get):
        ''' Return results of get_problem_html, as a simple dict for json-ing.
        { 'html': <the-html> }

            Used if we want to reconfirm we have the right thing e.g. after
            several AJAX calls.
        ''' 
        return {'html' : self.get_problem_html(encapsulate=False)}

    @staticmethod
    def make_dict_of_responses(get):
        '''Make dictionary of student responses (aka "answers")
        get is POST dictionary.
        '''
        answers = dict()
        for key in get:
            # e.g. input_resistor_1 ==> resistor_1
            _, _, name = key.partition('_')
            answers[name] = get[key]

        return answers

    def check_problem(self, get):
        ''' Checks whether answers to a problem are correct, and
            returns a map of correct/incorrect answers:

            {'success' : bool,
             'contents' : html}
            '''
        event_info = dict()
        event_info['state'] = self.lcp.get_state()
        event_info['filename'] = self.filename

        answers = self.make_dict_of_responses(get)

        event_info['answers'] = answers

        # Too late. Cannot submit
        if self.closed():
            event_info['failure'] = 'closed'
            self.tracker('save_problem_check_fail', event_info)
            # TODO (vshnayder): probably not 404?
            raise self.system.exception404

        # Problem submitted. Student should reset before checking
        # again.
        if self.lcp.done and self.rerandomize == "always":
            event_info['failure'] = 'unreset'
            self.tracker('save_problem_check_fail', event_info)
            raise self.system.exception404

        try:
            old_state = self.lcp.get_state()
            lcp_id = self.lcp.problem_id
            correct_map = self.lcp.grade_answers(answers)
        except StudentInputError as inst:
            # TODO (vshnayder): why is this line here?
            #self.lcp = LoncapaProblem(self.filestore.open(self.filename),
            #                          id=lcp_id, state=old_state, system=self.system)
            traceback.print_exc()
            return {'success': inst.message}
        except Exception, err:
            # TODO: why is this line here?
            #self.lcp = LoncapaProblem(self.filestore.open(self.filename),
            #                          id=lcp_id, state=old_state, system=self.system)
            if self.DEBUG:
                msg = "Error checking problem: " + str(err)
                msg += '\nTraceback:\n' + traceback.format_exc()
                return {'success':msg}
                
            traceback.print_exc()
            raise Exception,"error in capa_module"

        self.attempts = self.attempts + 1
        self.lcp.done = True

        # success = correct if ALL questions in this problem are correct
        success = 'correct'
        for answer_id in correct_map:
            if not correct_map.is_correct(answer_id):
                success = 'incorrect'

        event_info['correct_map'] = correct_map.get_dict()	# log this in the tracker
        event_info['success'] = success
        self.tracker('save_problem_check', event_info)

        try:
            html = self.get_problem_html(encapsulate=False)	# render problem into HTML
        except Exception,err:
            log.error('failed to generate html')
            raise

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
        event_info['filename'] = self.filename

        answers = self.make_dict_of_responses(get)
        event_info['answers'] = answers

        # Too late. Cannot submit
        if self.closed():
            event_info['failure'] = 'closed'
            self.tracker('save_problem_fail', event_info)
            return {'success': False,
                    'error': "Problem is closed"}

        # Problem submitted. Student should reset before saving
        # again.
        if self.lcp.done and self.rerandomize == "always":
            event_info['failure'] = 'done'
            self.tracker('save_problem_fail', event_info)
            return {'success' : False,
                    'error' : "Problem needs to be reset prior to save."}

        self.lcp.student_answers = answers

        # TODO: should this be save_problem_fail?  Looks like success to me...
        self.tracker('save_problem_fail', event_info)
        return {'success': True}

    def reset_problem(self, get):
        ''' Changes problem state to unfinished -- removes student answers,
            and causes problem to rerender itself.

            Returns problem html as { 'html' : html-string }.
        ''' 
        event_info = dict()
        event_info['old_state'] = self.lcp.get_state()
        event_info['filename'] = self.filename

        if self.closed():
            event_info['failure'] = 'closed'
            self.tracker('reset_problem_fail', event_info)
            return "Problem is closed"

        if not self.lcp.done:
            event_info['failure'] = 'not_done'
            self.tracker('reset_problem_fail', event_info)
            return "Refresh the page and make an attempt before resetting."

        self.lcp.do_reset()
        if self.rerandomize == "always":
            # reset random number generator seed (note the self.lcp.get_state() in next line)
            self.lcp.seed=None
            
        self.lcp = LoncapaProblem(self.filestore.open(self.filename),
                                  self.item_id, self.lcp.get_state(), system=self.system)

        event_info['new_state'] = self.lcp.get_state()
        self.tracker('reset_problem', event_info)

        return {'html' : self.get_problem_html(encapsulate=False)}
