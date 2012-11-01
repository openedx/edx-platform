import copy
from fs.errors import ResourceNotFoundError
import logging
import os
import sys
from lxml import etree
from lxml.html import rewrite_links
from path import path
import json
from progress import Progress

from .x_module import XModule
from pkg_resources import resource_string
from .xml_module import XmlDescriptor, name_to_pathname
from .editing_module import EditingDescriptor
from .stringify import stringify_children
from .html_checker import check_html
from xmodule.modulestore import Location

from xmodule.contentstore.content import XASSET_SRCREF_PREFIX, StaticContent

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

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, complex):
            return "{real:.7g}{imag:+.7g}*j".format(real=obj.real, imag=obj.imag)
        return json.JSONEncoder.default(self, obj)


class SelfAssessmentModule(XModule):
    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/selfassessment/display.coffee')
    ]
    }
    js_module_name = "SelfAssessment"

    def get_html(self):
        # cdodge: perform link substitutions for any references to course static content (e.g. images)
        return rewrite_links(self.html, self.rewrite_content_links)

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
            instance_state, shared_state, **kwargs)

        dom2=etree.fromstring("<selfassessment>" + self.definition['data'] + "</selfassessment>")
        self.rubric="<br/><br/>" + ''.join([etree.tostring(child) for child in only_one(dom2.xpath('rubric'))])
        self.problem=''.join([etree.tostring(child) for child in only_one(dom2.xpath('problem'))])
        problem_form=('<section class="sa-wrapper"><textarea name="answer" '
                      'id="answer" cols="50" rows="5"/><br/>'
                      '<input type="button" value="Check" id ="show" name="show" url="{0}"/>'
                      '<p id="rubric"></p></section><br/><br/>').format(self.location)

        rubric_form=('<br/><br/>Please assess your performance given the above rubric: <br/>'
                     '<br/><section class="sa-wrapper"><select name="assessment" id="assessment">'
                     '<option value="incorrect">Incorrect</option><option value="correct">'
                     'Correct</option></select><br/>'
                     '<input type="button" value="Save" id="save" name="save" url="{0}"/>'
                     '<p id="save_message"></p></section><br/><br/>').format(self.location)



        self.problem=''.join([self.problem,problem_form])
        self.rubric=''.join([self.rubric,rubric_form])
        self.html = self.problem
        self.answer=""
        self.score=0
        self.top_score=1
        self.submit_message=etree.tostring(dom2.xpath('submitmessage')[0])

        self.attempts = 0
        self.max_attempts = self.metadata.get('attempts', None)
        if self.max_attempts is not None:
            self.max_attempts = int(self.max_attempts)
        else:
            self.max_attempts=1

        self.correctness="incorrect"
        self.done=False
        if instance_state is not None:
            instance_state = json.loads(instance_state)
            log.debug(instance_state)

        if instance_state is not None and 'attempts' in instance_state:
            self.attempts = instance_state['attempts']

        if instance_state is not None and 'student_answers' in instance_state:
            self.answer=instance_state['student_answers']

        if instance_state is not None and 'done' in instance_state:
            self.done=instance_state['done']

        if instance_state is not None and 'correct_map' in instance_state:
            if 'self_assess' in instance_state['correct_map']:
                self.score=instance_state['correct_map']['self_assess']['npoints']
                self.correctness=instance_state['correct_map']['self_assess']['correctness']



    def get_score(self):
        return self.score

    def max_score(self):
        return self.top_score

    def get_progress(self):
        ''' For now, just return score / max_score
        '''
        score = self.get_score()
        total = self.max_score()
        if total > 0:
            try:
                return Progress(score, total)
            except Exception as err:
                log.exception("Got bad progress")
                return None
        return None


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
            'sa_show': self.show_rubric,
            'sa_save': self.save_problem,
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

    def show_rubric(self,get):
        self.answer=get.keys()[0]
        log.debug(self.answer)
        return {'success': True, 'rubric' : self.rubric}

    def save_problem(self, get):
        '''
        Save the passed in answers.
        Returns a dict { 'success' : bool, ['error' : error-msg]},
        with the error key only present if success is False.
        '''

        self.correctness=get.keys()[0].lower()
        log.debug(self.correctness)
        points=0
        if self.correctness=="correct" :
            points=1
        event_info = dict()
        self.done=True
        event_info['state'] = {'seed': 1,
                              'student_answers': self.answer,
                              'correct_map': {'self_assess' : {'correctness': self.correctness,
                                               'npoints': points,
                                               'msg': "",
                                               'hint': "",
                                               'hintmode': "",
                                               'queuestate': "",
                                               }},
                              'done': True}

        event_info['problem_id'] = self.location.url()

        event_info['answers'] = self.answer

        self.attempts = self.attempts + 1

        self.system.track_function('save_problem_succeed', event_info)

        return {'success': True, 'message' : self.submit_message}

    def get_instance_state(self):
        points=0
        if self.correctness=="correct" :
            points=1
        state= {'seed': 1,
                       'student_answers': self.answer,
                       'correct_map': {'self_assess' : {'correctness': self.correctness,
                                                        'npoints': points,
                                                        'msg': "",
                                                        'hint': "",
                                                        'hintmode': "",
                                                        'queuestate': "",
                                                        }},
                       'done': self.done}
        state['attempts'] = self.attempts
        return json.dumps(state)


class SelfAssessmentDescriptor(XmlDescriptor, EditingDescriptor):
    """
    Module for putting raw html in a course
    """
    mako_template = "widgets/html-edit.html"
    module_class = SelfAssessmentModule
    filename_extension = "xml"

    stores_state = True
    has_score = True
    template_dir_name = "html"

    js = {'coffee': [resource_string(__name__, 'js/src/html/edit.coffee')]}
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
