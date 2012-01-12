import random, numpy, math, scipy
from util import contextualize_text
from calc import evaluator
import random, math
from django.conf import settings

# TODO: Should be the same object as in capa_problem
global_context={'random':random,
                'numpy':numpy,
                'math':math,
                'scipy':scipy}

class numericalresponse(object):
    def __init__(self, xml, context):
        self.xml = xml
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        self.correct_answer = float(self.correct_answer)
        self.tolerance = xml.xpath('//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                                   id=xml.get('id'))[0]
        self.tolerance = contextualize_text(self.tolerance, context)
        self.tolerance = evaluator(dict(),dict(),self.tolerance)
        self.answer_id = xml.xpath('//*[@id=$id]//textline/@id',
                                   id=xml.get('id'))[0]

    def grade(self, student_answers):
        ''' Display HTML for a numeric response '''
        student_answer = student_answers[self.answer_id]
        error = abs(evaluator(dict(),dict(),student_answer) - self.correct_answer)
        allowed_error = abs(self.correct_answer*self.tolerance)
        if error <= allowed_error:
            return {self.answer_id:'correct'}
        else:
            return {self.answer_id:'incorrect'}

    def get_answers(self):
        return {self.answer_id:self.correct_answer}

class customresponse(object):
    def __init__(self, xml, context):
        self.xml = xml
        ## CRITICAL TODO: Should cover all entrytypes
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
        print "YY", self.answer_ids
        print "XX", student_answers
        submission = [student_answers[k] for k in sorted(self.answer_ids)]
        self.context.update({'submission':submission})
        print self.code
        exec self.code in global_context, self.context
        return  zip(sorted(self.answer_ids), self.context['correct'])

    def get_answers(self):
        # Since this is explicitly specified in the problem, this will 
        # be handled by capa_problem
        return {}


class formularesponse(object):
    def __init__(self, xml, context):
        self.xml = xml
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        self.samples = contextualize_text(xml.get('samples'), context)
        self.tolerance = xml.xpath('//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                                   id=xml.get('id'))[0]
        self.tolerance = contextualize_text(self.tolerance, context)
        self.tolerance = evaluator(dict(),dict(),self.tolerance)
        self.answer_id = xml.xpath('//*[@id=$id]//textline/@id',
                                   id=xml.get('id'))[0]
        self.context = context


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
            instructor_result = evaluator(instructor_variables,dict(),self.correct_answer)
            student_result = evaluator(student_variables,dict(),student_answers[self.answer_id])
            if math.isnan(student_result) or math.isinf(student_result):
                return {self.answer_id:"incorrect"}
            if abs( student_result - instructor_result ) > self.tolerance:
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
