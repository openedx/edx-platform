#
# File:   courseware/capa/responsetypes.py
#
'''
Problem response evaluation.  Handles checking of student responses, of a variety of types.

Used by capa_problem.py
'''

# standard library imports
import json
import math
import numbers
import numpy
import random
import re
import requests
import scipy
import traceback
import copy
import abc

# specific library imports
from calc import evaluator, UndefinedVariable
from django.conf import settings
from util import contextualize_text
from lxml import etree
from lxml.etree import Element
from lxml.html.soupparser import fromstring as fromstring_bs	# uses Beautiful Soup!!! FIXME?

# local imports
import calc
import eia


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

class GenericResponse(object):
    __metaclass__=abc.ABCMeta

    @abc.abstractmethod
    def grade(self, student_answers):
        pass

    @abc.abstractmethod
    def get_answers(self):
        pass

    #not an abstract method because plenty of responses will not want to preprocess anything, and we should not require that they override this method.
    def preprocess_response(self):
        pass

#Every response type needs methods "grade" and "get_answers"     

class MultipleChoiceResponse(GenericResponse):
    '''
    Example: 

    <multiplechoiceresponse direction="vertical" randomize="yes">
     <choicegroup type="MultipleChoice">
        <choice location="random" name="1" correct="false"><span>`a+b`<br/></span></choice>
        <choice location="random" name="2" correct="true"><span><math>a+b^2</math><br/></span></choice>
        <choice location="random" name="3" correct="false"><math>a+b+c</math></choice>
        <choice location="bottom" name="4" correct="false"><math>a+b+d</math></choice>
     </choicegroup>
    </multiplechoiceresponse>

    TODO: handle direction and randomize

    '''
    def __init__(self, xml, context, system=None):
        self.xml = xml
        self.correct_choices = xml.xpath('//*[@id=$id]//choice[@correct="true"]',
                                    id=xml.get('id'))
        self.correct_choices = [choice.get('name') for choice in self.correct_choices]
        self.context = context

        self.answer_id = xml.xpath('//*[@id=$id]//choicegroup/@id',
                                   id=xml.get('id'))
        if not len(self.answer_id) == 1:
            raise Exception("should have exactly one choice group per multiplechoicceresponse")
        self.answer_id=self.answer_id[0]

    def grade(self, student_answers):
        if self.answer_id in student_answers and student_answers[self.answer_id] in self.correct_choices:
            return {self.answer_id:'correct'}
        else:
            return {self.answer_id:'incorrect'}

    def get_answers(self):
        return {self.answer_id:self.correct_choices}

    def preprocess_response(self):
        i=0
        for response in self.xml.xpath("choicegroup"):
            response.set("type", "MultipleChoice")
            for choice in list(response):
                if choice.get("name") == None:
                    choice.set("name", "choice_"+str(i))
                    i+=1
                else:
                    choice.set("name", "choice_"+choice.get("name"))
        
class TrueFalseResponse(MultipleChoiceResponse):
    def preprocess_response(self):
        i=0
        for response in self.xml.xpath("choicegroup"):
            response.set("type", "TrueFalse")
            for choice in list(response):
                if choice.get("name") == None:
                    choice.set("name", "choice_"+str(i))
                    i+=1
                else:
                    choice.set("name", "choice_"+choice.get("name"))
    
    def grade(self, student_answers):
        correct = set(self.correct_choices)
        answers = set(student_answers.get(self.answer_id, []))
        
        if correct == answers:
            return { self.answer_id : 'correct'}
        
        return {self.answer_id : 'incorrect'}


class NumericalResponse(GenericResponse):
    def __init__(self, xml, context, system=None):
        self.xml = xml
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        try:
            self.tolerance_xml = xml.xpath('//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                                           id=xml.get('id'))[0]
            self.tolerance = contextualize_text(self.tolerance_xml, context)
        except Exception,err:
            self.tolerance = 0
        try:
            self.answer_id = xml.xpath('//*[@id=$id]//textline/@id',
                                       id=xml.get('id'))[0]
        except Exception, err:
            self.answer_id = None

    def grade(self, student_answers):
        ''' Display HTML for a numeric response '''
        student_answer = student_answers[self.answer_id]
        try:
            correct = compare_with_tolerance (evaluator(dict(),dict(),student_answer), complex(self.correct_answer), self.tolerance)
        # We should catch this explicitly. 
        # I think this is just pyparsing.ParseException, calc.UndefinedVariable:
        # But we'd need to confirm
        except: 
            raise StudentInputError('Invalid input -- please use a number only')

        if correct:
            return {self.answer_id:'correct'}
        else:
            return {self.answer_id:'incorrect'}

    def get_answers(self):
        return {self.answer_id:self.correct_answer}

#-----------------------------------------------------------------------------

class CustomResponse(GenericResponse):
    '''
    Custom response.  The python code to be run should be in <answer>...</answer>.  Example:

    <customresponse>
    <startouttext/>
    <br/>
    Suppose that \(I(t)\) rises from \(0\) to \(I_S\) at a time \(t_0 \neq 0\)
    In the space provided below write an algebraic expression for \(I(t)\).
    <br/>
    <textline size="5" correct_answer="IS*u(t-t0)" />
    <endouttext/>
    <answer type="loncapa/python">
    correct=['correct']
    try:
        r = str(submission[0])
    except ValueError:
        correct[0] ='incorrect'
        r = '0'
    if not(r=="IS*u(t-t0)"):
        correct[0] ='incorrect'
    </answer>
    </customresponse>
    
    Alternatively, the check function can be defined in <script>...</script>  Example:

<script type="loncapa/python"><![CDATA[

def sympy_check2():
  messages[0] = '%s:%s' % (submission[0],fromjs[0].replace('<','&lt;'))
  #messages[0] = str(answers)
  correct[0] = 'correct'

]]>
</script>

  <customresponse cfn="sympy_check2" type="cs" expect="2.27E-39" dojs="math" size="30" answer="2.27E-39">
    <textline size="40" dojs="math" />
    <responseparam description="Numerical Tolerance" type="tolerance" default="0.00001" name="tol"/>
  </customresponse>

    '''
    def __init__(self, xml, context, system=None):
        self.xml = xml
        ## CRITICAL TODO: Should cover all entrytypes
        ## NOTE: xpath will look at root of XML tree, not just 
        ## what's in xml. @id=id keeps us in the right customresponse. 
        self.answer_ids = xml.xpath('//*[@id=$id]//textline/@id',
                                    id=xml.get('id'))
        self.context = context
        answer_list = xml.xpath('//*[@id=$id]//answer',
                           id=xml.get('id'))
        if len(answer_list):
            answer=answer_list[0]
        else: 
            raise Exception("Invalid custom response -- no checker code")

        answer_src = answer.get('src')
        if answer_src != None:
            self.code = open(settings.DATA_DIR+'src/'+answer_src).read()
        else:
            self.code = answer.text

    def grade(self, student_answers):
        '''
        student_answers is a dict with everything from request.POST, but with the first part
        of each key removed (the string before the first "_").
        '''
        submission = [student_answers[k] for k in sorted(self.answer_ids)]
        self.context.update({'submission':submission})
        exec self.code in global_context, self.context
        return  zip(sorted(self.answer_ids), self.context['correct'])

    def get_answers(self):
        # Since this is explicitly specified in the problem, this will 
        # be handled by capa_problem
        return {}

#-----------------------------------------------------------------------------

class ExternalResponse(GenericResponse):
    '''
    Grade the student's input using an external server.
    
    Typically used by coding problems.
    '''
    def __init__(self, xml, context, system=None):
        self.xml = xml
        self.answer_ids = xml.xpath('//*[@id=$id]//textbox/@id|//*[@id=$id]//textline/@id',
                                    id=xml.get('id'))
        self.context = context
        answer = xml.xpath('//*[@id=$id]//answer',
                           id=xml.get('id'))[0]

        answer_src = answer.get('src')
        if answer_src != None:
            self.code = open(settings.DATA_DIR+'src/'+answer_src).read()
        else:
            self.code = answer.text

        self.tests = xml.get('answer')

    def grade(self, student_answers):
        submission = [student_answers[k] for k in sorted(self.answer_ids)]
        self.context.update({'submission':submission})

        xmlstr = etree.tostring(self.xml, pretty_print=True)

        payload = {'xml': xmlstr, 
				   ### Question: Is this correct/what we want? Shouldn't this be a json.dumps? 
          	       'LONCAPA_student_response': ''.join(submission), 
                   'LONCAPA_correct_answer': self.tests,
                   'processor' : self.code,
                   }

        # call external server; TODO: get URL from settings.py
        r = requests.post("http://eecs1.mit.edu:8889/pyloncapa",data=payload)

        rxml = etree.fromstring(r.text)         # response is XML; prase it
        ad = rxml.find('awarddetail').text
        admap = {'EXACT_ANS':'correct',         # TODO: handle other loncapa responses
        	 'WRONG_FORMAT': 'incorrect',
                 }
        self.context['correct'] = ['correct']
        if ad in admap:
            self.context['correct'][0] = admap[ad]

        # self.context['correct'] = ['correct','correct']
        correct_map = dict(zip(sorted(self.answer_ids), self.context['correct']))
        
        # TODO: separate message for each answer_id?
        correct_map['msg'] = rxml.find('message').text.replace('&nbsp;','&#160;')  # store message in correct_map

        return  correct_map

    def get_answers(self):
        # Since this is explicitly specified in the problem, this will 
        # be handled by capa_problem
        return {}

class StudentInputError(Exception):
    pass

#-----------------------------------------------------------------------------

class FormulaResponse(GenericResponse):
    def __init__(self, xml, context, system=None):
        self.xml = xml
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        self.samples = contextualize_text(xml.get('samples'), context)
        try:
            self.tolerance_xml = xml.xpath('//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                                           id=xml.get('id'))[0]
            self.tolerance = contextualize_text(self.tolerance_xml, context)
        except Exception,err:
            self.tolerance = 0

        try:
            self.answer_id = xml.xpath('//*[@id=$id]//textline/@id',
                                       id=xml.get('id'))[0]
        except Exception, err:
            self.answer_id = None
            raise Exception, "[courseware.capa.responsetypes.FormulaResponse] Error: missing answer_id!!"

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
            for var in ranges:				# ranges give numerical ranges for testing
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
            if numpy.isnan(student_result) or numpy.isinf(student_result):
                return {self.answer_id:"incorrect"}
            if not compare_with_tolerance(student_result, instructor_result, self.tolerance):
                return {self.answer_id:"incorrect"}
 
        return {self.answer_id:"correct"}

    def strip_dict(self, d):
        ''' Takes a dict. Returns an identical dict, with all non-word
        keys and all non-numeric values stripped out. All values also
        converted to float. Used so we can safely use Python contexts.
        ''' 
        d=dict([(k, numpy.complex(d[k])) for k in d if type(k)==str and \
                    k.isalnum() and \
                    isinstance(d[k], numbers.Number)])
        return d

    def get_answers(self):
        return {self.answer_id:self.correct_answer}

#-----------------------------------------------------------------------------

class SchematicResponse(GenericResponse):
    def __init__(self, xml, context, system=None):
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

#-----------------------------------------------------------------------------

class ImageResponse(GenericResponse):
    """
    Handle student response for image input: the input is a click on an image,
    which produces an [x,y] coordinate pair.  The click is correct if it falls
    within a region specified.  This region is nominally a rectangle.

    Lon-CAPA requires that each <imageresponse> has a <foilgroup> inside it.  That
    doesn't make sense to me (Ike).  Instead, let's have it such that <imageresponse>
    should contain one or more <imageinput> stanzas. Each <imageinput> should specify 
    a rectangle, given as an attribute, defining the correct answer.

    Example:

    <imageresponse>
      <imageinput src="image1.jpg" width="200" height="100" rectangle="(10,10)-(20,30)" />
      <imageinput src="image2.jpg" width="210" height="130" rectangle="(12,12)-(40,60)" />
    </imageresponse>

    """
    def __init__(self, xml, context, system=None):
        self.xml = xml
        self.context = context
        self.ielements = xml.findall('imageinput')
        self.answer_ids = [ie.get('id')  for ie in self.ielements]

    def grade(self, student_answers):
        correct_map = {}
        expectedset = self.get_answers()

        for aid in self.answer_ids:	# loop through IDs of <imageinput> fields in our stanza
            given = student_answers[aid]	# this should be a string of the form '[x,y]'

            # parse expected answer
            # TODO: Compile regexp on file load
            m = re.match('[\(\[]([0-9]+),([0-9]+)[\)\]]-[\(\[]([0-9]+),([0-9]+)[\)\]]',expectedset[aid].strip().replace(' ',''))
            if not m:
                msg = 'Error in problem specification! cannot parse rectangle in %s' % (etree.tostring(self.ielements[aid],
                                                                                                       pretty_print=True))
                raise Exception,'[capamodule.capa.responsetypes.imageinput] '+msg
            (llx,lly,urx,ury) = [int(x) for x in m.groups()]
                
            # parse given answer
            m = re.match('\[([0-9]+),([0-9]+)]',given.strip().replace(' ',''))
            if not m:
                raise Exception,'[capamodule.capa.responsetypes.imageinput] error grading %s (input=%s)' % (err,aid,given)
            (gx,gy) = [int(x) for x in m.groups()]
            
            if settings.DEBUG:
                print "[capamodule.capa.responsetypes.imageinput] llx,lly,urx,ury=",(llx,lly,urx,ury)
                print "[capamodule.capa.responsetypes.imageinput] gx,gy=",(gx,gy)

            # answer is correct if (x,y) is within the specified rectangle
            if (llx <= gx <= urx) and (lly <= gy <= ury):
                correct_map[aid] = 'correct'
            else:
                correct_map[aid] = 'incorrect'
        if settings.DEBUG:
            print "[capamodule.capa.responsetypes.imageinput] correct_map=",correct_map
        return correct_map

    def get_answers(self):
        return dict([(ie.get('id'),ie.get('rectangle')) for ie in self.ielements])
