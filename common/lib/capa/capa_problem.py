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

import copy
import logging
import math
import numpy
import os
import random
import re
import scipy
import struct

from lxml import etree
from xml.sax.saxutils import unescape

import calc
from correctmap import CorrectMap
import eia
import inputtypes
from util import contextualize_text

# to be replaced with auto-registering
import responsetypes

# dict of tagname, Response Class -- this should come from auto-registering
response_tag_dict = dict([(x.response_tag,x) for x in responsetypes.__all__])

entry_types = ['textline', 'schematic', 'choicegroup', 'textbox', 'imageinput', 'optioninput']
solution_types = ['solution']    			# extra things displayed after "show answers" is pressed
response_properties = ["responseparam", "answer"]    	# these get captured as student responses

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
html_problem_semantics = ["responseparam", "answer", "script","hintgroup"]

#log = logging.getLogger(__name__)
log = logging.getLogger('mitx.common.lib.capa.capa_problem')

#-----------------------------------------------------------------------------
# main class for this module

class LoncapaProblem(object):
    '''
    Main class for capa Problems.
    '''

    def __init__(self, fileobject, id, state=None, seed=None, system=None):
        '''
        Initializes capa Problem.  The problem itself is defined by the XML file
        pointed to by fileobject.

        Arguments:

         - filesobject  : an OSFS instance: see fs.osfs
         - id           : string used as the identifier for this problem; often a filename (no spaces)
         - state        : student state (represented as a dict)
         - seed         : random number generator seed (int)
         - system       : I4xSystem instance which provides OS, rendering, and user context 

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

        self.fileobject = fileobject    	# save problem file object, so we can use for debugging information later
        if getattr(system, 'DEBUG', False):	# get the problem XML string from the problem file
            log.info("[courseware.capa.capa_problem.lcp.init]  fileobject = %s" % fileobject)
        file_text = fileobject.read()
        file_text = re.sub("startouttext\s*/", "text", file_text)   # Convert startouttext and endouttext to proper <text></text>
        file_text = re.sub("endouttext\s*/", "/text", file_text)

        self.tree = etree.XML(file_text)	# parse problem XML file into an element tree

        # construct script processor context (eg for customresponse problems)
        self.context = self.extract_context(self.tree, seed=self.seed)

        # pre-parse the XML tree: modifies it to add ID's and perform some in-place transformations
        # this also creates the dict (self.responders) of Response instances for each question in the problem.
        # the dict has keys = xml subtree of Response, values = Response instance
        self.preprocess_problem(self.tree, answer_map=self.student_answers)

    def do_reset(self):
        '''
        Reset internal state to unfinished, with no answers
        '''
        self.student_answers = dict()
        self.correct_map = CorrectMap()
        self.done = False

    def __unicode__(self):
        return u"LoncapaProblem ({0})".format(self.fileobject)

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
	We do this by counting the number of answers available for each question
        in the problem.  If the Response for a question has a get_max_score() method
        then we call that and add its return value to the count.  That can be
        used to give complex problems (eg programming questions) multiple points.
        '''
        maxscore = 0
        for responder in self.responders.values():
            if hasattr(responder,'get_max_score'):
                try:
                    maxscore += responder.get_max_score()
                except Exception, err:
                    log.error('responder %s failed to properly return from get_max_score()' % responder)
                    raise
            else:
                try:
                    maxscore += len(responder.get_answers())
                except:
                    log.error('responder %s failed to properly return get_answers()' % responder)
                    raise
        return maxscore

    def get_score(self):
        '''
        Compute score for this problem.  The score is the number of points awarded.
        Returns an integer, from 0 to get_max_score().
        '''
        correct = 0
        for key in self.correct_map:
            try:
                correct += self.correct_map.get_npoints(key)
            except Exception,err:
                log.error('key=%s, correct_map = %s' % (key,self.correct_map))
                raise

        if (not self.student_answers) or len(self.student_answers) == 0:
            return {'score': 0,
                    'total': self.get_max_score()}
        else:
            return {'score': correct,
                    'total': self.get_max_score()}

    def grade_answers(self, answers):
        '''
        Grade student responses.  Called by capa_module.check_problem.
        answers is a dict of all the entries from request.POST, but with the first part
        of each key removed (the string before the first "_").

        Thus, for example, input_ID123 -> ID123, and input_fromjs_ID123 -> fromjs_ID123

        Calles the Response for each question in this problem, to do the actual grading.
        '''
        self.student_answers = answers
        oldcmap = self.correct_map				# old CorrectMap
        newcmap = CorrectMap()					# start new with empty CorrectMap
        log.debug('Responders: %s' % self.responders)
        for responder in self.responders.values():
            results = responder.evaluate_answers(answers,oldcmap)      # call the responsetype instance to do the actual grading
            newcmap.update(results)
        self.correct_map = newcmap
        log.debug('%s: in grade_answers, answers=%s, cmap=%s' % (self,answers,newcmap))
        return newcmap

    def get_question_answers(self):
        """Returns a dict of answer_ids to answer values. If we cannot generate
        an answer (this sometimes happens in customresponses), that answer_id is
        not included. Called by "show answers" button JSON request
        (see capa_module)
        """
        answer_map = dict()
        for responder in self.responders.values():
            results = responder.get_answers()
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
        for responder in self.responders.values():
            answer_ids.append(responder.get_answers().keys())
        return answer_ids

    def get_html(self):
        '''
        Main method called externally to get the HTML to be rendered for this capa Problem.
        '''
        return contextualize_text(etree.tostring(self.extract_html(self.tree)), self.context)

    # ======= Private Methods Below ========

    def extract_context(self, tree, seed=struct.unpack('i', os.urandom(4))[0]):  # private
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

        for script in tree.findall('.//script'):
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
            try:
                exec code in context, context        # use "context" for global context; thus defs in code are global within code
            except Exception:
                log.exception("Error while execing code: " + code)
        return context

    def extract_html(self, problemtree):  # private
        '''
        Main (private) function which converts Problem XML tree to HTML.
        Calls itself recursively.

        Returns Element tree of XHTML representation of problemtree.
        Calls render_html of Response instances to render responses into XHTML.

        Used by get_html.
        '''
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
                                                                       'hint' : hint,
                                                                       'hintmode' : hintmode,
                                                                       }
                                                          },
                                                   use='capa_input')
            return render_object.get_html()  # function(problemtree, value, status, msg) # render the special response (textline, schematic,...)

        if problemtree in self.responders:		# let each Response render itself
            return self.responders[problemtree].render_html(self.extract_html)

        tree = etree.Element(problemtree.tag)
        for item in problemtree:
            item_xhtml = self.extract_html(item)		# nothing special: recurse
            if item_xhtml is not None:
                    tree.append(item_xhtml)

        if tree.tag in html_transforms:
            tree.tag = html_transforms[problemtree.tag]['tag']
        else:
            for (key, value) in problemtree.items():	# copy attributes over if not innocufying
                tree.set(key, value)

        tree.text = problemtree.text
        tree.tail = problemtree.tail

        return tree

    def preprocess_problem(self, tree, answer_map=dict()):  # private
        '''
        Assign IDs to all the responses
        Assign sub-IDs to all entries (textline, schematic, etc.)
        Annoted correctness and value
        In-place transformation

        Also create capa Response instances for each responsetype and save as self.responders
        '''
        response_id = 1
	self.responders = {}
        for response in tree.xpath('//' + "|//".join(response_tag_dict)):
            response_id_str = self.problem_id + "_" + str(response_id)
            response.set('id',response_id_str)				# create and save ID for this response
            response_id += 1

            answer_id = 1
            inputfields = tree.xpath("|".join(['//' + response.tag + '[@id=$id]//' + x for x in (entry_types + solution_types)]),
                                    id=response_id_str)
            for entry in inputfields:			                # assign one answer_id for each entry_type or solution_type
                entry.attrib['response_id'] = str(response_id)
                entry.attrib['answer_id'] = str(answer_id)
                entry.attrib['id'] = "%s_%i_%i" % (self.problem_id, response_id, answer_id)
                answer_id = answer_id + 1

            responder = response_tag_dict[response.tag](response, inputfields, self.context, self.system) # instantiate capa Response
	    self.responders[response] = responder				# save in list in self

        # <solution>...</solution> may not be associated with any specific response; give IDs for those separately
        # TODO: We should make the namespaces consistent and unique (e.g. %s_problem_%i).
        solution_id = 1
        for solution in tree.findall('.//solution'):
            solution.attrib['id'] = "%s_solution_%i" % (self.problem_id, solution_id)
            solution_id += 1
