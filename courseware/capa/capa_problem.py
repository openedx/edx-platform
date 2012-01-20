import random, numpy, math, scipy
import struct, os
import re
from lxml import etree
from lxml.etree import Element
import copy
from mako.template import Template
from content_parser import xpath_remove
import calc, eia

from util import contextualize_text

from inputtypes import textline, schematic
from responsetypes import numericalresponse, formularesponse, customresponse, schematicresponse

response_types = {'numericalresponse':numericalresponse, 
                  'formularesponse':formularesponse,
                  'customresponse':customresponse,
                  'schematicresponse':schematicresponse}
entry_types = ['textline', 'schematic']
response_properties = ["responseparam", "answer"]
# How to convert from original XML to HTML
# We should do this with xlst later
html_transforms = {'problem': {'tag':'div'},
                   "numericalresponse": {'tag':'span'}, 
                   "customresponse": {'tag':'span'}, 
                   "schematicresponse": {'tag':'span'}, 
                   "formularesponse": {'tag':'span'}, 
                   "text": {'tag':'span'}}

global_context={'random':random,
                'numpy':numpy,
                'math':math,
                'scipy':scipy, 
                'calc':calc, 
                'eia':eia}

# These should be removed from HTML output, including all subelements
html_problem_semantics = ["responseparam", "answer", "script"]
# These should be removed from HTML output, but keeping subelements
html_skip = ["numericalresponse", "customresponse", "schematicresponse", "formularesponse", "text"]
# These should be transformed
html_special_response = {"textline":textline.render,
                         "schematic":schematic.render}

class LoncapaProblem(object):
    def __init__(self, filename, id=None, state=None):
        ## Initialize class variables from state
        self.seed = None
        self.student_answers = dict()
        self.correct_map = dict()
        self.done = False
        self.filename = filename

        if id!=None:
            self.problem_id = id
        else:
            self.problem_id = filename

        if state!=None:
            if 'seed' in state:
                self.seed = state['seed']
            if 'student_answers' in state:
                self.student_answers = state['student_answers']
            if 'correct_map' in state:
                self.correct_map = state['correct_map']
            if 'done' in state:
                self.done = state['done']

        # TODO: Does this deplete the Linux entropy pool? Is this fast enough?
        if self.seed == None:
            self.seed=struct.unpack('i', os.urandom(4))[0]

        ## Parse XML file
        file_text = open(filename).read()
        # Convert startouttext and endouttext to proper <text></text>
        # TODO: Do with XML operations
        file_text = re.sub("startouttext\s*/","text",file_text)
        file_text = re.sub("endouttext\s*/","/text",file_text)
        self.tree = etree.XML(file_text)

        self.preprocess_problem(self.tree, correct_map=self.correct_map, answer_map = self.student_answers)
        self.context = self.extract_context(self.tree, seed=self.seed)

    def get_state(self):
        ''' Stored per-user session data neeeded to: 
            1) Recreate the problem
            2) Populate any student answers. '''
        return {'seed':self.seed, 
                'student_answers':self.student_answers,
                'correct_map':self.correct_map, 
                'done':self.done}

    def get_max_score(self):
        sum = 0 
        for et in entry_types: 
            sum = sum + self.tree.xpath('count(//'+et+')')
        return int(sum)

    def get_score(self):
        correct=0
        for key in self.correct_map:
            if self.correct_map[key] == u'correct':
                correct += 1
        if self.student_answers == None or len(self.student_answers)==0:
            return {'score':0,
                    'total':self.get_max_score()}
        else:
            return {'score':correct,
                    'total':self.get_max_score()}

    def grade_answers(self, answers):
        self.student_answers = answers
        context=self.extract_context(self.tree)
        self.correct_map = dict()
        problems_simple = self.extract_problems(self.tree)
        for response in problems_simple:
            grader = response_types[response.tag](response, self.context)
            results = grader.grade(answers)
            self.correct_map.update(results)

        return self.correct_map

    def get_question_answers(self):
        context=self.extract_context(self.tree)
        answer_map = dict()
        problems_simple = self.extract_problems(self.tree)
        for response in problems_simple:
            responder = response_types[response.tag](response, self.context)
            results = responder.get_answers()
            answer_map.update(results)

        for entry in problems_simple.xpath("//"+"|//".join(response_properties+entry_types)):
            answer = entry.get('correct_answer')
            if answer != None:
                answer_map[entry.get('id')] = contextualize_text(answer, self.context())

        return answer_map

    # ======= Private ========

    def extract_context(self, tree, seed = struct.unpack('i', os.urandom(4))[0]):  # private
        ''' Problem XML goes to Python execution context. Runs everything in script tags '''
        random.seed(self.seed)
        context = dict()
        for script in tree.xpath('/problem/script'):
            exec script.text in global_context, context
        return context

    def get_html(self):
        return contextualize_text(etree.tostring(self.extract_html(self.tree)[0]), self.context)

    def extract_html(self, problemtree):  # private
        ''' Helper function for get_html. Recursively converts XML tree to HTML
        '''
        if problemtree.tag in html_problem_semantics:
            return

        if problemtree.tag in html_special_response:
            status = "unsubmitted"
            if problemtree.get('id') in self.correct_map:
                status = self.correct_map[problemtree.get('id')]

            value = ""
            if self.student_answers != None and problemtree.get('id') in self.student_answers:
                value = self.student_answers[problemtree.get('id')]

            return html_special_response[problemtree.tag](problemtree, value, status) #TODO

        tree=Element(problemtree.tag)
        for item in problemtree:
            subitems = self.extract_html(item)
            if subitems != None: 
                for subitem in subitems:
                    tree.append(subitem)
        for (key,value) in problemtree.items():
            tree.set(key, value)

        tree.text=problemtree.text
        tree.tail=problemtree.tail

        if problemtree.tag in html_transforms:
            tree.tag=html_transforms[problemtree.tag]['tag']

        # TODO: Fix. This loses Element().tail
        #if problemtree.tag in html_skip:
        #    return tree

        return [tree]

    def preprocess_problem(self, tree, correct_map=dict(), answer_map=dict()): # private
        ''' Assign IDs to all the responses 
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
            for entry in tree.xpath("|".join(['//'+response.tag+'[@id=$id]//'+x for x in entry_types]), 
                                    id=response_id_str):
                entry.attrib['response_id'] = str(response_id)
                entry.attrib['answer_id'] = str(answer_id)
                entry.attrib['id'] = "%s_%i_%i"%(self.problem_id, response_id, answer_id)
                answer_id=answer_id+1

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
