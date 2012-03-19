import json
import math
import numpy
import random
import scipy
import traceback

from calc import evaluator, UndefinedVariable
from django.conf import settings
from util import contextualize_text

import calc
import eia

# TODO: Should be the same object as in capa_problem
global_context={'random':random,
                'numpy':numpy,
                'math':math,
                'scipy':scipy, 
                'calc':calc, 
                'eia':eia}


def compare_with_tolerance(v1, v2, tol):
    ''' Compare v1 to v2 with maximum tolerance tol
    tol is relative if it ends in %; otherwise, it is absolute
    '''
    relative = "%" in tol
    if relative: 
        tolerance_rel = evaluator(dict(),dict(),tol[:-1]) * 0.01
        tolerance = tolerance_rel * max(abs(v1), abs(v2))
    else: 
        tolerance = evaluator(dict(),dict(),tol)
    return abs(v1-v2) <= tolerance

class numericalresponse(object):
    def __init__(self, xml, context):
        self.xml = xml
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        self.correct_answer = float(self.correct_answer)
        self.tolerance_xml = xml.xpath('//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                                   id=xml.get('id'))[0]
        self.tolerance = contextualize_text(self.tolerance_xml, context)
        self.answer_id = xml.xpath('//*[@id=$id]//textline/@id',
                                   id=xml.get('id'))[0]

    def grade(self, student_answers):
        ''' Display HTML for a numeric response '''
        student_answer = student_answers[self.answer_id]
        try:
            correct = compare_with_tolerance (evaluator(dict(),dict(),student_answer), self.correct_answer, self.tolerance)
        except:
            raise StudentInputError('Invalid input -- please use a number only')

        if correct:
            return {self.answer_id:'correct'}
        else:
            return {self.answer_id:'incorrect'}

    def get_answers(self):
        return {self.answer_id:self.correct_answer}

class customresponse(object):
    def __init__(self, xml, context):
        self.xml = xml
        ## CRITICAL TODO: Should cover all entrytypes
        ## NOTE: xpath will look at root of XML tree, not just 
        ## what's in xml. @id=id keeps us in the right customresponse. 
        self.answer_ids = xml.xpath('//*[@id=$id]//textline/@id',
                                    id=xml.get('id'))
        self.context = context
        answer = xml.xpath('//*[@id=$id]//answer',
                           id=xml.get('id'))[0]
        answer_src = answer.get('src')
        if answer_src != None:
            self.code = open(settings.DATA_DIR+'src/'+answer_src).read()
        else:
            self.code = answer.text

    def grade(self, student_answers):
        submission = [student_answers[k] for k in sorted(self.answer_ids)]
        self.context.update({'submission':submission})
        exec self.code in global_context, self.context
        return  zip(sorted(self.answer_ids), self.context['correct'])

    def get_answers(self):
        # Since this is explicitly specified in the problem, this will 
        # be handled by capa_problem
        return {}

class StudentInputError(Exception):
    pass

class formularesponse(object):
    def __init__(self, xml, context):
        self.xml = xml
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        self.samples = contextualize_text(xml.get('samples'), context)
        self.tolerance_xml = xml.xpath('//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                                   id=xml.get('id'))[0]
        self.tolerance = contextualize_text(self.tolerance_xml, context)
        self.answer_id = xml.xpath('//*[@id=$id]//textline/@id',
                                   id=xml.get('id'))[0]
        self.context = context
        ts = xml.get('type')
        if ts == None:
            typeslist = []
        else:
            typeslist = ts.split(',')
        if 'ci' in typeslist: # Case insensitive
            self.case_sensitive = False
        elif 'cs' in typeslist: # Case sensitive
            self.case_sensitive = True
        else: # Default
            self.case_sensitive = False


    def grade(self, student_answers):
        variables=self.samples.split('@')[0].split(',')
        numsamples=int(self.samples.split('@')[1].split('#')[1])
        sranges=zip(*map(lambda x:map(float, x.split(",")), 
                         self.samples.split('@')[1].split('#')[0].split(':')))

        ranges=dict(zip(variables, sranges))
        correct = True
        for i in range(numsamples):
            instructor_variables = self.strip_dict(dict(self.context))
            student_variables = dict()
            for var in ranges:
                value = random.uniform(*ranges[var])
                instructor_variables[str(var)] = value
                student_variables[str(var)] = value
            instructor_result = evaluator(instructor_variables,dict(),self.correct_answer, cs = self.case_sensitive)
            try: 
                #print student_variables,dict(),student_answers[self.answer_id]
                student_result = evaluator(student_variables,dict(),
                                           student_answers[self.answer_id], 
                                           cs = self.case_sensitive)
            except UndefinedVariable as uv:
                raise StudentInputError(uv.message+" not permitted in answer")
            except:
                #traceback.print_exc()
                raise StudentInputError("Error in formula")
            if math.isnan(student_result) or math.isinf(student_result):
                return {self.answer_id:"incorrect"}
            if not compare_with_tolerance(student_result, instructor_result, self.tolerance):
                return {self.answer_id:"incorrect"}
 
        return {self.answer_id:"correct"}

    def strip_dict(self, d):
        ''' Takes a dict. Returns an identical dict, with all non-word
        keys and all non-numeric values stripped out. All values also
        converted to float. Used so we can safely use Python contexts.
        ''' 
        d=dict([(k, float(d[k])) for k in d if type(k)==str and \
                    k.isalnum() and \
                    (type(d[k]) == float or type(d[k]) == int) ])
        return d

    def get_answers(self):
        return {self.answer_id:self.correct_answer}

class schematicresponse(object):
    def __init__(self, xml, context):
        self.xml = xml
        self.answer_ids = xml.xpath('//*[@id=$id]//schematic/@id',
                                    id=xml.get('id'))
        self.context = context
        answer = xml.xpath('//*[@id=$id]//answer',
                           id=xml.get('id'))[0]
        answer_src = answer.get('src')
        if answer_src != None:
            self.code = open(settings.DATA_DIR+'src/'+answer_src).read()
        else:
            self.code = answer.text

    def grade(self, student_answers):
        submission = [json.loads(student_answers[k]) for k in sorted(self.answer_ids)]
        self.context.update({'submission':submission})
        exec self.code in global_context, self.context
        return  zip(sorted(self.answer_ids), self.context['correct'])

    def get_answers(self):
        # Since this is explicitly specified in the problem, this will 
        # be handled by capa_problem
        return {}
