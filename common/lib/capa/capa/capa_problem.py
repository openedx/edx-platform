#
# File:   capa/capa_problem.py
#
# Nomenclature:
#
# A capa Problem is a collection of text and capa Response questions.  Each Response may have one or more
# Input entry fields.  The capa Problem may include a solution.
#
'''
Main module which shows problems (of "capa" type).

This is used by capa_module.
'''

from __future__ import division

from datetime import datetime
import json
import logging
import math
import numpy
import os
import random
import re
import scipy
import struct
import sys

from lxml import etree
from xml.sax.saxutils import unescape

import calc
from correctmap import CorrectMap
import eia
import inputtypes
from util import contextualize_text, convert_files_to_filenames
import xqueue_interface

# to be replaced with auto-registering
import responsetypes

# dict of tagname, Response Class -- this should come from auto-registering
response_tag_dict = dict([(x.response_tag, x) for x in responsetypes.__all__])

entry_types = ['textline', 'schematic', 'textbox', 'imageinput', 'optioninput', 'choicegroup', 'radiogroup', 'checkboxgroup', 'filesubmission', 'javascriptinput']
solution_types = ['solution']    			# extra things displayed after "show answers" is pressed
response_properties = ["codeparam", "responseparam", "answer"]    	# these get captured as student responses

# special problem tags which should be turned into innocuous HTML
html_transforms = {'problem': {'tag': 'div'},
                   "text": {'tag': 'span'},
                   "math": {'tag': 'span'},
                   }

global_context = {'random': random,
                  'numpy': numpy,
                  'math': math,
                  'scipy': scipy,
                  'calc': calc,
                  'eia': eia}

# These should be removed from HTML output, including all subelements
html_problem_semantics = ["codeparam", "responseparam", "answer", "script", "hintgroup"]

log = logging.getLogger('mitx.' + __name__)

#-----------------------------------------------------------------------------
# main class for this module


class LoncapaProblem(object):
    '''
    Main class for capa Problems.
    '''

    def __init__(self, problem_text, id, state=None, seed=None, system=None):
        '''
        Initializes capa Problem.

        Arguments:

         - problem_text (string): xml defining the problem
         - id           (string): identifier for this problem; often a filename (no spaces)
         - state        (dict): student state
         - seed         (int): random number generator seed (int)
         - system       (ModuleSystem): ModuleSystem instance which provides OS, rendering, and user context

        '''

        ## Initialize class variables from state
        self.do_reset()
        self.problem_id = id
        self.system = system
        self.seed = seed

        if state:
            if 'seed' in state:
                self.seed = state['seed']
            if 'student_answers' in state:
                self.student_answers = state['student_answers']
            if 'correct_map' in state:
                self.correct_map.set_dict(state['correct_map'])
            if 'done' in state:
                self.done = state['done']

        # TODO: Does this deplete the Linux entropy pool? Is this fast enough?
        if not self.seed:
            self.seed = struct.unpack('i', os.urandom(4))[0]

        problem_text = re.sub("startouttext\s*/", "text", problem_text)   # Convert startouttext and endouttext to proper <text></text>
        problem_text = re.sub("endouttext\s*/", "/text", problem_text)
        self.problem_text = problem_text

        self.tree = etree.XML(problem_text)  # parse problem XML file into an element tree
        self._process_includes()		# handle any <include file="foo"> tags

        # construct script processor context (eg for customresponse problems)
        self.context = self._extract_context(self.tree, seed=self.seed)

        # pre-parse the XML tree: modifies it to add ID's and perform some in-place transformations
        # this also creates the dict (self.responders) of Response instances for each question in the problem.
        # the dict has keys = xml subtree of Response, values = Response instance
        self._preprocess_problem(self.tree)

        if not self.student_answers:  # True when student_answers is an empty dict
            self.set_initial_display()

    def do_reset(self):
        '''
        Reset internal state to unfinished, with no answers
        '''
        self.student_answers = dict()
        self.correct_map = CorrectMap()
        self.done = False

    def set_initial_display(self):
        initial_answers = dict()
        for responder in self.responders.values():
            if hasattr(responder, 'get_initial_display'):
                initial_answers.update(responder.get_initial_display())

        self.student_answers = initial_answers

    def __unicode__(self):
        return u"LoncapaProblem ({0})".format(self.problem_id)

    def get_state(self):
        ''' Stored per-user session data neeeded to:
            1) Recreate the problem
            2) Populate any student answers. '''

        return {'seed': self.seed,
                'student_answers': self.student_answers,
                'correct_map': self.correct_map.get_dict(),
                'done': self.done}

    def get_max_score(self):
        '''
        Return maximum score for this problem.
        '''
        maxscore = 0
        for response, responder in self.responders.iteritems():
            maxscore += responder.get_max_score()
        return maxscore

    def get_score(self):
        '''
        Compute score for this problem.  The score is the number of points awarded.
        Returns a dictionary {'score': integer, from 0 to get_max_score(),
                              'total': get_max_score()}.
        '''
        correct = 0
        for key in self.correct_map:
            try:
                correct += self.correct_map.get_npoints(key)
            except Exception:
                log.error('key=%s, correct_map = %s' % (key, self.correct_map))
                raise

        if (not self.student_answers) or len(self.student_answers) == 0:
            return {'score': 0,
                    'total': self.get_max_score()}
        else:
            return {'score': correct,
                    'total': self.get_max_score()}

    def update_score(self, score_msg, queuekey):
        '''
        Deliver grading response (e.g. from async code checking) to
            the specific ResponseType that requested grading

        Returns an updated CorrectMap
        '''
        cmap = CorrectMap()
        cmap.update(self.correct_map)
        for responder in self.responders.values():
            if hasattr(responder, 'update_score'):
                # Each LoncapaResponse will update its specific entries in cmap
                #   cmap is passed by reference
                responder.update_score(score_msg, cmap, queuekey)
        self.correct_map.set_dict(cmap.get_dict())
        return cmap

    def is_queued(self):
        '''
        Returns True if any part of the problem has been submitted to an external queue
        '''
        return any(self.correct_map.is_queued(answer_id) for answer_id in self.correct_map)


    def get_recentmost_queuetime(self):
        '''
        Returns a DateTime object that represents the timestamp of the most recent queueing request, or None if not queued
        '''
        if not self.is_queued():
            return None

        # Get a list of timestamps of all queueing requests, then convert it to a DateTime object
        queuetime_strs = [self.correct_map.get_queuetime_str(answer_id)
                          for answer_id in self.correct_map 
                          if self.correct_map.is_queued(answer_id)]
        queuetimes = [datetime.strptime(qt_str, xqueue_interface.dateformat) for qt_str in queuetime_strs]

        return max(queuetimes)


    def grade_answers(self, answers):
        '''
        Grade student responses.  Called by capa_module.check_problem.
        answers is a dict of all the entries from request.POST, but with the first part
        of each key removed (the string before the first "_").

        Thus, for example, input_ID123 -> ID123, and input_fromjs_ID123 -> fromjs_ID123

        Calls the Response for each question in this problem, to do the actual grading.
        '''

        self.student_answers = convert_files_to_filenames(answers)

        oldcmap = self.correct_map				# old CorrectMap
        newcmap = CorrectMap()					# start new with empty CorrectMap
        # log.debug('Responders: %s' % self.responders)
        for responder in self.responders.values():                  # Call each responsetype instance to do actual grading
            if 'filesubmission' in responder.allowed_inputfields:   # File objects are passed only if responsetype
                                                                    #   explicitly allows for file submissions
                results = responder.evaluate_answers(answers, oldcmap)
            else:
                results = responder.evaluate_answers(convert_files_to_filenames(answers), oldcmap)
            newcmap.update(results)
        self.correct_map = newcmap
        # log.debug('%s: in grade_answers, answers=%s, cmap=%s' % (self,answers,newcmap))
        return newcmap

    def get_question_answers(self):
        """Returns a dict of answer_ids to answer values. If we cannot generate
        an answer (this sometimes happens in customresponses), that answer_id is
        not included. Called by "show answers" button JSON request
        (see capa_module)
        """
        answer_map = dict()
        for response in self.responders.keys():
            results = self.responder_answers[response]
            answer_map.update(results)                # dict of (id,correct_answer)

        # include solutions from <solution>...</solution> stanzas
        for entry in self.tree.xpath("//" + "|//".join(solution_types)):
            answer = etree.tostring(entry)
            if answer: answer_map[entry.get('id')] = answer

        log.debug('answer_map = %s' % answer_map)
        return answer_map

    def get_answer_ids(self):
        """Return the IDs of all the responses -- these are the keys used for
        the dicts returned by grade_answers and get_question_answers. (Though
        get_question_answers may only return a subset of these."""
        answer_ids = []
        for response in self.responders.keys():
            results = self.responder_answers[response]
            answer_ids.append(results.keys())
        return answer_ids

    def get_html(self):
        '''
        Main method called externally to get the HTML to be rendered for this capa Problem.
        '''
        return contextualize_text(etree.tostring(self._extract_html(self.tree)), self.context)

    # ======= Private Methods Below ========

    def _process_includes(self):
        '''
        Handle any <include file="foo"> tags by reading in the specified file and inserting it
        into our XML tree.  Fail gracefully if debugging.
        '''
        includes = self.tree.findall('.//include')
        for inc in includes:
            file = inc.get('file')
            if file is not None:
                try:
                    ifp = self.system.filestore.open(file)  # open using ModuleSystem OSFS filestore
                except Exception as err:
                    log.warning('Error %s in problem xml include: %s' % (
                            err, etree.tostring(inc, pretty_print=True)))
                    log.warning('Cannot find file %s in %s' % (
                            file, self.system.filestore))
                    # if debugging, don't fail - just log error
                    # TODO (vshnayder): need real error handling, display to users
                    if not self.system.get('DEBUG'):
                        raise
                    else:
                        continue
                try:
                    incxml = etree.XML(ifp.read())    # read in and convert to XML
                except Exception as err:
                    log.warning('Error %s in problem xml include: %s' % (
                            err, etree.tostring(inc, pretty_print=True)))
                    log.warning('Cannot parse XML in %s' % (file))
                    # if debugging, don't fail - just log error
                    # TODO (vshnayder): same as above
                    if not self.system.get('DEBUG'):
                        raise
                    else:
                        continue
                # insert new XML into tree in place of inlcude
                parent = inc.getparent()
                parent.insert(parent.index(inc), incxml)
                parent.remove(inc)
                log.debug('Included %s into %s' % (file, self.problem_id))

    def _extract_system_path(self, script):
        '''
        Extracts and normalizes additional paths for code execution.
        For now, there's a default path of data/course/code; this may be removed
        at some point.
        '''

        DEFAULT_PATH = ['code']

        # Separate paths by :, like the system path.
        raw_path = script.get('system_path', '').split(":") + DEFAULT_PATH

        # find additional comma-separated modules search path
        path = []

        for dir in raw_path:

            if not dir:
                continue

            # path is an absolute path or a path relative to the data dir
            dir = os.path.join(self.system.filestore.root_path, dir)
            abs_dir = os.path.normpath(dir)
            #log.debug("appending to path: %s" % abs_dir)
            path.append(abs_dir)

        return path

    def _extract_context(self, tree, seed=struct.unpack('i', os.urandom(4))[0]):  # private
        '''
        Extract content of <script>...</script> from the problem.xml file, and exec it in the
        context of this problem.  Provides ability to randomize problems, and also set
        variables for problem answer checking.

        Problem XML goes to Python execution context. Runs everything in script tags
        '''
        random.seed(self.seed)
        context = {'global_context': global_context}    	# save global context in here also
        context.update(global_context)            		# initialize context to have stuff in global_context
        context['__builtins__'] = globals()['__builtins__']    	# put globals there also
        context['the_lcp'] = self                		# pass instance of LoncapaProblem in
        context['script_code'] = ''

        self._execute_scripts(tree.findall('.//script'), context)

        return context

    def _execute_scripts(self, scripts, context):
        '''
        Executes scripts in the given context.
        '''
        original_path = sys.path

        for script in scripts:

            sys.path = original_path + self._extract_system_path(script)

            stype = script.get('type')
            if stype:
                if 'javascript' in stype:
                    continue    # skip javascript
                if 'perl' in stype:
                    continue        # skip perl
            # TODO: evaluate only python
            code = script.text
            XMLESC = {"&apos;": "'", "&quot;": '"'}
            code = unescape(code, XMLESC)
            context['script_code'] += code		# store code source in context
            try:
                exec code in context, context        	# use "context" for global context; thus defs in code are global within code
            except Exception as err:
                log.exception("Error while execing script code: " + code)
		msg = "Error while executing script code: %s" % str(err).replace('<','&lt;')
                raise responsetypes.LoncapaProblemError(msg)
            finally:
                sys.path = original_path

    def _extract_html(self, problemtree):  # private
        '''
        Main (private) function which converts Problem XML tree to HTML.
        Calls itself recursively.

        Returns Element tree of XHTML representation of problemtree.
        Calls render_html of Response instances to render responses into XHTML.

        Used by get_html.
        '''
        if problemtree.tag == 'script' and problemtree.get('type') and 'javascript' in problemtree.get('type'):
            # leave javascript intact.
            return problemtree

        if problemtree.tag in html_problem_semantics:
            return

        problemid = problemtree.get('id')    # my ID

        if problemtree.tag in inputtypes.get_input_xml_tags():

            status = "unsubmitted"
            msg = ''
            hint = ''
            hintmode = None
            if problemid in self.correct_map:
                pid = problemtree.get('id')
                status = self.correct_map.get_correctness(pid)
                msg = self.correct_map.get_msg(pid)
                hint = self.correct_map.get_hint(pid)
                hintmode = self.correct_map.get_hintmode(pid)

            value = ""
            if self.student_answers and problemid in self.student_answers:
                value = self.student_answers[problemid]

            # do the rendering
            render_object = inputtypes.SimpleInput(system=self.system,
                                                   xml=problemtree,
                                                   state={'value': value,
                                                          'status': status,
                                                          'id': problemtree.get('id'),
                                                          'feedback': {'message': msg,
                                                                       'hint': hint,
                                                                       'hintmode': hintmode,
                                                                       }
                                                          },
                                                   use='capa_input')
            return render_object.get_html()  # function(problemtree, value, status, msg) # render the special response (textline, schematic,...)

        if problemtree in self.responders:		# let each Response render itself
            return self.responders[problemtree].render_html(self._extract_html)

        tree = etree.Element(problemtree.tag)
        for item in problemtree:
            item_xhtml = self._extract_html(item)		# nothing special: recurse
            if item_xhtml is not None:
                    tree.append(item_xhtml)

        if tree.tag in html_transforms:
            tree.tag = html_transforms[problemtree.tag]['tag']
        else:
            for (key, value) in problemtree.items():	 # copy attributes over if not innocufying
                tree.set(key, value)

        tree.text = problemtree.text
        tree.tail = problemtree.tail

        return tree

    def _preprocess_problem(self, tree):  # private
        '''
        Assign IDs to all the responses
        Assign sub-IDs to all entries (textline, schematic, etc.)
        Annoted correctness and value
        In-place transformation

        Also create capa Response instances for each responsetype and save as self.responders

        Obtain all responder answers and save as self.responder_answers dict (key = response)
        '''
        response_id = 1
        self.responders = {}
        for response in tree.xpath('//' + "|//".join(response_tag_dict)):
            response_id_str = self.problem_id + "_" + str(response_id)
            response.set('id', response_id_str)				# create and save ID for this response
            response_id += 1

            answer_id = 1
            inputfields = tree.xpath("|".join(['//' + response.tag + '[@id=$id]//' + x for x in (entry_types + solution_types)]),
                                    id=response_id_str)
            for entry in inputfields:			                # assign one answer_id for each entry_type or solution_type
                entry.attrib['response_id'] = str(response_id)
                entry.attrib['answer_id'] = str(answer_id)
                entry.attrib['id'] = "%s_%i_%i" % (self.problem_id, response_id, answer_id)
                answer_id = answer_id + 1

            responder = response_tag_dict[response.tag](response, inputfields, self.context, self.system)  # instantiate capa Response
            self.responders[response] = responder                               # save in list in self

        # get responder answers (do this only once, since there may be a performance cost, eg with externalresponse)
        self.responder_answers = {}
        for response in self.responders.keys():
            try:
                self.responder_answers[response] = self.responders[response].get_answers()
            except:
                log.debug('responder %s failed to properly return get_answers()' % self.responders[response])  # FIXME
                raise

        # <solution>...</solution> may not be associated with any specific response; give IDs for those separately
        # TODO: We should make the namespaces consistent and unique (e.g. %s_problem_%i).
        solution_id = 1
        for solution in tree.findall('.//solution'):
            solution.attrib['id'] = "%s_solution_%i" % (self.problem_id, solution_id)
            solution_id += 1
