#
# File:   courseware/capa/capa_problem.py
#
'''
Main module which shows problems (of "capa" type).

This is used by capa_module.
'''

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
from lxml.etree import Element
from xml.sax.saxutils import escape, unescape

from mako.template import Template

from util import contextualize_text
import inputtypes

from responsetypes import NumericalResponse, FormulaResponse, CustomResponse, SchematicResponse, MultipleChoiceResponse,  StudentInputError, TrueFalseResponse, ExternalResponse,ImageResponse,OptionResponse

import calc
import eia

log = logging.getLogger("mitx.courseware")

response_types = {'numericalresponse':NumericalResponse, 
                  'formularesponse':FormulaResponse,
                  'customresponse':CustomResponse,
                  'schematicresponse':SchematicResponse,
                  'externalresponse':ExternalResponse,
                  'multiplechoiceresponse':MultipleChoiceResponse,
                  'truefalseresponse':TrueFalseResponse,
                  'imageresponse':ImageResponse,
                  'optionresponse':OptionResponse,
                  }
entry_types = ['textline', 'schematic', 'choicegroup','textbox','imageinput','optioninput']
solution_types = ['solution']	# extra things displayed after "show answers" is pressed
response_properties = ["responseparam", "answer"]	# these get captured as student responses

# How to convert from original XML to HTML
# We should do this with xlst later
html_transforms = {'problem': {'tag':'div'},
                   "numericalresponse": {'tag':'span'}, 
                   "customresponse": {'tag':'span'}, 
                   "externalresponse": {'tag':'span'},
                   "schematicresponse": {'tag':'span'}, 
                   "formularesponse": {'tag':'span'}, 
                   "multiplechoiceresponse": {'tag':'span'}, 
                   "text": {'tag':'span'},
                   "math": {'tag':'span'},
                   }

global_context={'random':random,
                'numpy':numpy,
                'math':math,
                'scipy':scipy, 
                'calc':calc, 
                'eia':eia}

# These should be removed from HTML output, including all subelements
html_problem_semantics = ["responseparam", "answer", "script"]
# These should be removed from HTML output, but keeping subelements
html_skip = ["numericalresponse", "customresponse", "schematicresponse", "formularesponse", "text","externalresponse"]

# removed in MC
## These should be transformed
#html_special_response = {"textline":inputtypes.textline.render,
#                         "schematic":inputtypes.schematic.render,
#                         "textbox":inputtypes.textbox.render,
#                         "formulainput":inputtypes.jstextline.render,
#                         "solution":inputtypes.solution.render,
#                         }

class LoncapaProblem(object):
    def __init__(self, fileobject, id, state=None, seed=None, system=None):
        ## Initialize class variables from state
        self.seed = None
        self.student_answers = dict()
        self.correct_map = dict()
        self.done = False
        self.problem_id = id
        self.system = system

        if seed is not None:
            self.seed = seed

        if state:
            if 'seed' in state:
                self.seed = state['seed']
            if 'student_answers' in state:
                self.student_answers = state['student_answers']
            if 'correct_map' in state:
                self.correct_map = state['correct_map']
            if 'done' in state:
                self.done = state['done']

        # TODO: Does this deplete the Linux entropy pool? Is this fast enough?
        if not self.seed:
            self.seed=struct.unpack('i', os.urandom(4))[0]

        ## Parse XML file
        file_text = fileobject.read()
        self.fileobject = fileobject	# save it, so we can use for debugging information later
        # Convert startouttext and endouttext to proper <text></text>
        # TODO: Do with XML operations
        file_text = re.sub("startouttext\s*/","text",file_text)
        file_text = re.sub("endouttext\s*/","/text",file_text)
        self.tree = etree.XML(file_text)

        self.preprocess_problem(self.tree, correct_map=self.correct_map, answer_map = self.student_answers)
        self.context = self.extract_context(self.tree, seed=self.seed)
        for response in self.tree.xpath('//'+"|//".join(response_types)):
            responder = response_types[response.tag](response, self.context, self.system)
            responder.preprocess_response()

    def get_state(self):
        ''' Stored per-user session data neeeded to: 
            1) Recreate the problem
            2) Populate any student answers. '''
        return {'seed':self.seed, 
                'student_answers':self.student_answers,
                'correct_map':self.correct_map, 
                'done':self.done}

    def get_max_score(self):
        '''
        TODO: multiple points for programming problems.
        '''
        sum = 0 
        for et in entry_types: 
            sum = sum + self.tree.xpath('count(//'+et+')')
        return int(sum)

    def get_score(self):
        correct=0
        for key in self.correct_map:
            if self.correct_map[key] == u'correct':
                correct += 1
        if (not self.student_answers) or len(self.student_answers)==0:
            return {'score':0,
                    'total':self.get_max_score()}
        else:
            return {'score':correct,
                    'total':self.get_max_score()}

    def grade_answers(self, answers):
        '''
        Grade student responses.  Called by capa_module.check_problem.
        answers is a dict of all the entries from request.POST, but with the first part
        of each key removed (the string before the first "_").

        Thus, for example, input_ID123 -> ID123, and input_fromjs_ID123 -> fromjs_ID123
        '''
        self.student_answers = answers
        context=self.extract_context(self.tree)
        self.correct_map = dict()
        problems_simple = self.extract_problems(self.tree)
        for response in problems_simple:
            grader = response_types[response.tag](response, self.context, self.system)
            results = grader.get_score(answers)		# call the responsetype instance to do the actual grading
            self.correct_map.update(results)
        return self.correct_map

    def get_question_answers(self):
        '''
        Make a dict of (id,correct_answer) entries, for all the problems. 
        Called by "show answers" button JSON request (see capa_module)
        '''
        context=self.extract_context(self.tree)
        answer_map = dict()
        problems_simple = self.extract_problems(self.tree)	# purified (flat) XML tree of just response queries
        for response in problems_simple:
            responder = response_types[response.tag](response, self.context, self.system)	# instance of numericalresponse, customresponse,...
            results = responder.get_answers()
            answer_map.update(results)				# dict of (id,correct_answer) 

        # example for the following: <textline size="5" correct_answer="saturated" />
        for entry in problems_simple.xpath("//"+"|//".join(response_properties+entry_types)):
            answer = entry.get('correct_answer')		# correct answer, when specified elsewhere, eg in a textline
            if answer:
                answer_map[entry.get('id')] = contextualize_text(answer, self.context)

        # include solutions from <solution>...</solution> stanzas
        # Tentative merge; we should figure out how we want to handle hints and solutions
        for entry in self.tree.xpath("//"+"|//".join(solution_types)):
            answer = etree.tostring(entry)
            if answer:
                answer_map[entry.get('id')] = answer

        return answer_map

    # ======= Private ========

    def extract_context(self, tree, seed = struct.unpack('i', os.urandom(4))[0]):  # private
        '''
        Extract content of <script>...</script> from the problem.xml file, and exec it in the
        context of this problem.  Provides ability to randomize problems, and also set
        variables for problem answer checking.
        
        Problem XML goes to Python execution context. Runs everything in script tags
        '''
        random.seed(self.seed)
		### IKE: Why do we need these two lines? 
        context = {'global_context':global_context}	# save global context in here also
        global_context['context'] = context		# and put link to local context in the global one

        #for script in tree.xpath('/problem/script'):
        for script in tree.findall('.//script'):
            code = script.text
            XMLESC = {"&apos;": "'", "&quot;": '"'}
            code = unescape(code,XMLESC)
            try:
                exec code in global_context, context
            except Exception,err:
                print "[courseware.capa.capa_problem.extract_context] error %s" % err
                print "in doing exec of this code:",code
        return context

    def get_html(self):
        return contextualize_text(etree.tostring(self.extract_html(self.tree)[0]), self.context)

    def extract_html(self, problemtree):  # private
        ''' Helper function for get_html. Recursively converts XML tree to HTML
        '''
        if problemtree.tag in html_problem_semantics:
            return

        problemid = problemtree.get('id')	# my ID
        
        # used to be
        # if problemtree.tag in html_special_response:
        
        if problemtree.tag in inputtypes.get_input_xml_tags():
            # status is currently the answer for the problem ID for the input element,
            # but it will turn into a dict containing both the answer and any associated message
            # for the problem ID for the input element.
            status = "unsubmitted"
            if problemid in self.correct_map:
                status = self.correct_map[problemtree.get('id')]

            value = ""
            if self.student_answers and problemid in self.student_answers:
                value = self.student_answers[problemid]

            #### This code is a hack. It was merged to help bring two branches
            #### in sync, but should be replaced. msg should be passed in a 
            #### response_type
            # prepare the response message, if it exists in correct_map
            if 'msg' in self.correct_map:
                msg = self.correct_map['msg']
            elif ('msg_%s' % problemid) in self.correct_map:
                msg = self.correct_map['msg_%s' % problemid]
            else:
                msg = ''

            #if settings.DEBUG:
            #    print "[courseware.capa.capa_problem.extract_html] msg = ",msg

            # do the rendering
            # This should be broken out into a helper function
            # that handles all input objects
            render_object = inputtypes.SimpleInput(system = self.system, 
                                                   xml = problemtree,
                                                   state = {'value':value, 
                                                            'status': status, 
                                                            'id':problemtree.get('id'), 
                                                            'feedback':{'message':msg}
                                                            },
                                                   use = 'capa_input')
            return render_object.get_html() #function(problemtree, value, status, msg) # render the special response (textline, schematic,...)

        tree=Element(problemtree.tag)
        for item in problemtree:
            subitems = self.extract_html(item)
            if subitems is not None:
                for subitem in subitems:
                    tree.append(subitem)
        for (key,value) in problemtree.items():
            tree.set(key, value)

        tree.text=problemtree.text
        tree.tail=problemtree.tail

        if problemtree.tag in html_transforms:
            tree.tag=html_transforms[problemtree.tag]['tag']
            # Reset attributes. Otherwise, we get metadata in HTML
            # (e.g. answers) 
            # TODO: We should remove and not zero them.
            # I'm not sure how to do that quickly with lxml
            for k in tree.keys():
                tree.set(k,"")

        # TODO: Fix. This loses Element().tail
        #if problemtree.tag in html_skip:
        #    return tree
        return [tree]

    def preprocess_problem(self, tree, correct_map=dict(), answer_map=dict()): # private
        '''
        Assign IDs to all the responses 
        Assign sub-IDs to all entries (textline, schematic, etc.)
        Annoted correctness and value
        In-place transformation
        '''
        response_id = 1
        for response in tree.xpath('//'+"|//".join(response_types)):
            response_id_str=self.problem_id+"_"+str(response_id)
            response.attrib['id']=response_id_str
            if response_id not in correct_map:
                correct = 'unsubmitted'
            response.attrib['state'] = correct
            response_id = response_id + 1
            answer_id = 1
            for entry in tree.xpath("|".join(['//'+response.tag+'[@id=$id]//'+x for x in (entry_types + solution_types)]), 
                                    id=response_id_str):
                # assign one answer_id for each entry_type or solution_type 
                entry.attrib['response_id'] = str(response_id)
                entry.attrib['answer_id'] = str(answer_id)
                entry.attrib['id'] = "%s_%i_%i"%(self.problem_id, response_id, answer_id)
                answer_id=answer_id+1

        # <solution>...</solution> may not be associated with any specific response; give IDs for those separately
		# TODO: We should make the namespaces consistent and unique (e.g. %s_problem_%i). 
        solution_id = 1
        for solution in tree.findall('.//solution'):
            solution.attrib['id'] =  "%s_solution_%i"%(self.problem_id, solution_id)
            solution_id += 1

    def extract_problems(self, problem_tree):
        ''' Remove layout from the problem, and give a purified XML tree of just the problems '''
        problem_tree=copy.deepcopy(problem_tree)
        tree=Element('problem')
        for response in problem_tree.xpath("//"+"|//".join(response_types)):
            newresponse = copy.copy(response)
            for e in newresponse: 
                newresponse.remove(e)
            # copy.copy is needed to make xpath work right. Otherwise, it starts at the root
            # of the tree. We should figure out if there's some work-around
            for e in copy.copy(response).xpath("//"+"|//".join(response_properties+entry_types)):
                newresponse.append(e)
                
            tree.append(newresponse)
        return tree

if __name__=='__main__':
    problem_id='simpleFormula'
    filename = 'simpleFormula.xml'

    problem_id='resistor'
    filename = 'resistor.xml'

    
    lcp = LoncapaProblem(filename, problem_id)
    
    context = lcp.extract_context(lcp.tree)
    problem = lcp.extract_problems(lcp.tree)
    print lcp.grade_problems({'resistor_2_1':'1.0','resistor_3_1':'2.0'})
    #print lcp.grade_problems({'simpleFormula_2_1':'3*x^3'})
#numericalresponse(problem, context)
    
#print etree.tostring((lcp.tree))
    print '============'
    print
#print etree.tostring(lcp.extract_problems(lcp.tree))
    print lcp.get_html()
#print extract_context(tree)
    


    # def handle_fr(self, element):
    #     problem={"answer":self.contextualize_text(answer),
    #              "type":"formularesponse",
    #              "tolerance":evaluator({},{},self.contextualize_text(tolerance)),
    #              "sample_range":dict(zip(variables, sranges)),
    #              "samples_count": numsamples,
    #              "id":id,
    #     self.questions[self.lid]=problem        
