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
from lxml.html import rewrite_links
from pkg_resources import resource_string

from capa.capa_problem import LoncapaProblem
from capa.responsetypes import StudentInputError
from capa.util import convert_files_to_filenames
from progress import Progress
from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.exceptions import NotFoundError

log = logging.getLogger("mitx.courseware")

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


class SelfAssessmentModule(XModule):
    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/selfassessment/display.coffee')
    ]
    }
    js_module_name = "SelfAssessmentModule"

    def get_html(self):
        # cdodge: perform link substitutions for any references to course static content (e.g. images)
        return rewrite_links(self.html, self.rewrite_content_links)

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
            instance_state, shared_state, **kwargs)

        dom2 = etree.fromstring(definition['data'])

        self.attempts = 0
        self.max_attempts = None

        self.max_attempts = self.metadata.get('attempts', None)
        if self.max_attempts is not None:
            self.max_attempts = int(self.max_attempts)

        if instance_state is not None:
            instance_state = json.loads(instance_state)
        if instance_state is not None and 'attempts' in instance_state:
            self.attempts = instance_state['attempts']

        self.name = only_one(dom2.xpath('/problem/@name'))

        self.rubric=etree.tostring(only_one(dom2.xpath("/rubric")))
        self.problem=etree.tostring(only_one(dom2.xpath("/problem")))

        self.lcp = LoncapaProblem(self.problem, self.location.html_id(),
            instance_state, seed=self.seed, system=self.system)

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
                warning  = '<div class="capa_reset">'\
                           '<h2>Warning: The problem has been reset to its initial state!</h2>'\
                           'The problem\'s state was corrupted by an invalid submission. '\
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
                except Exception, err: # Couldn't do it. Give up
                    log.exception(err)
                    raise

        content = {'name': self.display_name,
                   'html': html,
                   'weight': self.descriptor.weight,
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
        if self.rerandomize not in ["always", "onreset"]:
            reset_button = False

        # User hasn't submitted an answer yet -- we don't want resets
        if not self.lcp.done:
            reset_button = False

        # We may not need a "save" button if infinite number of attempts and
        # non-randomized. The problem author can force it. It's a bit weird for
        # randomization to control this; should perhaps be cleaned up.
        if (self.force_save_button == "false") and (self.max_attempts is None and self.rerandomize != "always"):
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

        # cdodge: OK, we have to do two rounds of url reference subsitutions
        # one which uses the 'asset library' that is served by the contentstore and the
        # more global /static/ filesystem based static content.
        # NOTE: rewrite_content_links is defined in XModule
        # This is a bit unfortunate and I'm sure we'll try to considate this into
        # a one step process.
        html = rewrite_links(html, self.rewrite_content_links)

        # now do the substitutions which are filesystem based, e.g. '/static/' prefixes
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

        parsed_answer=False
        if(answer[answers.keys()[0]]=="True"):
            parsed_answer=True

        # Too late. Cannot submit
        if self.closed():
            event_info['failure'] = 'closed'
            self.system.track_function('save_problem_check_fail', event_info)
            raise NotFoundError('Problem is closed')

        try:
            old_state = self.lcp.get_state()
            lcp_id = self.lcp.problem_id
            correct_map = self.lcp.grade_answers(answers)
            correct_map.set(correctness=parsed_answer)
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


class SelfAssessmentDescriptor(XmlDescriptor, EditingDescriptor):
    """
    Module for putting raw html in a course
    """
    mako_template = "widgets/html-edit.html"
    module_class = HtmlModule
    filename_extension = "xml"
    template_dir_name = "html"
    stores_state=True
    has_score=True

    js = {'coffee': [resource_string(__name__, 'js/src/selfassessment/edit.coffee')]}
    js_module_name = "HTMLEditingDescriptor"

    # VS[compat] TODO (cpennington): Delete this method once all fall 2012 course
    # are being edited in the cms
    @classmethod
    def backcompat_paths(cls, path):
        if path.endswith('.html.xml'):
            path = path[:-9] + '.html'  # backcompat--look for html instead of xml
        if path.endswith('.html.html'):
            path = path[:-5]            # some people like to include .html in filenames..
        candidates = []
        while os.sep in path:
            candidates.append(path)
            _, _, path = path.partition(os.sep)

        # also look for .html versions instead of .xml
        nc = []
        for candidate in candidates:
            if candidate.endswith('.xml'):
                nc.append(candidate[:-4] + '.html')
        return candidates + nc

    # NOTE: html descriptors are special.  We do not want to parse and
    # export them ourselves, because that can break things (e.g. lxml
    # adds body tags when it exports, but they should just be html
    # snippets that will be included in the middle of pages.

    @classmethod
    def load_definition(cls, xml_object, system, location):
        '''Load a descriptor from the specified xml_object:

        If there is a filename attribute, load it as a string, and
        log a warning if it is not parseable by etree.HTMLParser.

        If there is not a filename attribute, the definition is the body
        of the xml_object, without the root tag (do not want <html> in the
        middle of a page)
        '''
        filename = xml_object.get('filename')
        if filename is None:
            definition_xml = copy.deepcopy(xml_object)
            cls.clean_metadata_from_xml(definition_xml)
            return {'data': stringify_children(definition_xml)}
        else:
            # html is special.  cls.filename_extension is 'xml', but
            # if 'filename' is in the definition, that means to load
            # from .html
            # 'filename' in html pointers is a relative path
            # (not same as 'html/blah.html' when the pointer is in a directory itself)
            pointer_path = "{category}/{url_path}".format(category='html',
                url_path=name_to_pathname(location.name))
            base = path(pointer_path).dirname()
            #log.debug("base = {0}, base.dirname={1}, filename={2}".format(base, base.dirname(), filename))
            filepath = "{base}/{name}.html".format(base=base, name=filename)
            #log.debug("looking for html file for {0} at {1}".format(location, filepath))



            # VS[compat]
            # TODO (cpennington): If the file doesn't exist at the right path,
            # give the class a chance to fix it up. The file will be written out
            # again in the correct format.  This should go away once the CMS is
            # online and has imported all current (fall 2012) courses from xml
            if not system.resources_fs.exists(filepath):
                candidates = cls.backcompat_paths(filepath)
                #log.debug("candidates = {0}".format(candidates))
                for candidate in candidates:
                    if system.resources_fs.exists(candidate):
                        filepath = candidate
                        break

            try:
                with system.resources_fs.open(filepath) as file:
                    html = file.read()
                    # Log a warning if we can't parse the file, but don't error
                    if not check_html(html):
                        msg = "Couldn't parse html in {0}.".format(filepath)
                        log.warning(msg)
                        system.error_tracker("Warning: " + msg)

                    definition = {'data': html}

                    # TODO (ichuang): remove this after migration
                    # for Fall 2012 LMS migration: keep filename (and unmangled filename)
                    definition['filename'] = [ filepath, filename ]

                    return definition

            except (ResourceNotFoundError) as err:
                msg = 'Unable to load file contents at path {0}: {1} '.format(
                    filepath, err)
                # add more info and re-raise
                raise Exception(msg), None, sys.exc_info()[2]

    # TODO (vshnayder): make export put things in the right places.

    def definition_to_xml(self, resource_fs):
        '''If the contents are valid xml, write them to filename.xml.  Otherwise,
        write just <html filename="" [meta-attrs="..."]> to filename.xml, and the html
        string to filename.html.
        '''
        try:
            return etree.fromstring(self.definition['data'])
        except etree.XMLSyntaxError:
            pass

        # Not proper format.  Write html to file, return an empty tag
        pathname = name_to_pathname(self.url_name)
        pathdir = path(pathname).dirname()
        filepath = u'{category}/{pathname}.html'.format(category=self.category,
            pathname=pathname)

        resource_fs.makedir(os.path.dirname(filepath), allow_recreate=True)
        with resource_fs.open(filepath, 'w') as file:
            file.write(self.definition['data'])

        # write out the relative name
        relname = path(pathname).basename()

        elt = etree.Element('html')
        elt.set("filename", relname)
        return elt
