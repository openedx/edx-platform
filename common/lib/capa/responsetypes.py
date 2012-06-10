#
# File:   courseware/capa/responsetypes.py
#
'''
Problem response evaluation.  Handles checking of student responses, of a variety of types.

Used by capa_problem.py
'''

# standard library imports
import inspect
import json
import logging
import numbers
import numpy
import random
import re
import requests
import traceback
import abc

# specific library imports
from calc import evaluator, UndefinedVariable
from util import *
from lxml import etree
from lxml.html.soupparser import fromstring as fromstring_bs	# uses Beautiful Soup!!! FIXME?

#log = logging.getLogger(__name__)
log = logging.getLogger('mitx.common.lib.capa.responsetypes')

#-----------------------------------------------------------------------------
# Exceptions

class LoncapaProblemError(Exception):
    '''
    Error in specification of a problem
    '''
    pass

class ResponseError(Exception):
    '''
    Error for failure in processing a response
    '''
    pass

class StudentInputError(Exception):
    pass

#-----------------------------------------------------------------------------
#
# Main base class for CAPA responsetypes

class GenericResponse(object):
    '''
    Base class for CAPA responsetypes.  Each response type (ie a capa question,
    which is part of a capa problem) is represented as a superclass,
    which should provide the following methods:

      - get_score           : evaluate the given student answers, and return a CorrectMap
      - get_answers         : provide a dict of the expected answers for this problem
      
    In addition, these methods are optional:

      - get_max_score       : if defined, this is called to obtain the maximum score possible for this question
      - setup_response      : find and note the answer input field IDs for the response; called by __init__
      - render_html         : render this Response as HTML (must return XHTML compliant string)
      - __unicode__         : unicode representation of this Response

    Each response type may also specify the following attributes:

      - max_inputfields     : (int) maximum number of answer input fields (checked in __init__ if not None)
      - allowed_inputfields : list of allowed input fields (each a string) for this Response
      - required_attributes : list of required attributes (each a string) on the main response XML stanza

    '''
    __metaclass__=abc.ABCMeta # abc = Abstract Base Class

    max_inputfields = None
    allowed_inputfields = []
    required_attributes = []
    
    def __init__(self, xml, inputfields, context, system=None):
        '''
        Init is passed the following arguments:

          - xml         : ElementTree of this Response
          - inputfields : list of ElementTrees for each input entry field in this Response
          - context     : script processor context
          - system      : I4xSystem instance which provides OS, rendering, and user context 

        '''
        self.xml = xml
        self.inputfields = inputfields
        self.context = context
        self.system = system

        for abox in inputfields:
            if not abox.tag in self.allowed_inputfields:
                msg = "%s: cannot have input field %s" % (unicode(self),abox.tag)
                msg += "\nSee XML source line %s" % getattr(xml,'sourceline','<unavailable>')
                raise LoncapaProblemError(msg)

        if self.max_inputfields and len(inputfields)>self.max_inputfields:
            msg = "%s: cannot have more than %s input fields" % (unicode(self),self.max_inputfields)
            msg += "\nSee XML source line %s" % getattr(xml,'sourceline','<unavailable>')
            raise LoncapaProblemError(msg)

        for prop in self.required_attributes:
            if not xml.get(prop):
                msg = "Error in problem specification: %s missing required attribute %s" % (unicode(self),prop)
                msg += "\nSee XML source line %s" % getattr(xml,'sourceline','<unavailable>')
                raise LoncapaProblemError(msg)

        self.answer_ids = [x.get('id') for x in self.inputfields]
        if self.max_inputfields==1:
            self.answer_id = self.answer_ids[0]		# for convenience

        self.default_answer_map = {}			# dict for default answer map (provided in input elements)
        for entry in self.inputfields:
            answer = entry.get('correct_answer')        
            if answer:
                self.default_answer_map[entry.get('id')] = contextualize_text(answer, self.context)

        if hasattr(self,'setup_response'):
            self.setup_response()

    def render_html(self,renderer):
        '''
        Return XHTML Element tree representation of this Response.

        Arguments:

          - renderer : procedure which produces HTML given an ElementTree
        '''
        tree = etree.Element('span')			# render ourself as a <span> + our content
        for item in self.xml:
            item_xhtml = renderer(item)			# call provided procedure to do the rendering
            if item_xhtml is not None: tree.append(item_xhtml)
        tree.tail = self.xml.tail
        return tree

    @abc.abstractmethod
    def get_score(self, student_answers):
        '''
        Return a CorrectMap for the answers expected vs given.  This includes
        (correctness, npoints, msg) for each answer_id.
        '''
        pass

    @abc.abstractmethod
    def get_answers(self):
        '''
        Return a dict of (answer_id,answer_text) for each answer for this question.
        '''
        pass

    def setup_response(self):
        pass

    def __unicode__(self):
        return u'LoncapaProblem Response %s' % self.xml.tag

#-----------------------------------------------------------------------------

class MultipleChoiceResponse(GenericResponse):
    # TODO: handle direction and randomize
    snippets = [{'snippet': '''<multiplechoiceresponse direction="vertical" randomize="yes">
     <choicegroup type="MultipleChoice">
        <choice location="random" correct="false"><span>`a+b`<br/></span></choice>
        <choice location="random" correct="true"><span><math>a+b^2</math><br/></span></choice>
        <choice location="random" correct="false"><math>a+b+c</math></choice>
        <choice location="bottom" correct="false"><math>a+b+d</math></choice>
     </choicegroup>
    </multiplechoiceresponse>
    '''}]

    max_inputfields = 1
    allowed_inputfields = ['choicegroup']

    def setup_response(self):
        self.mc_setup_response()	# call secondary setup for MultipleChoice questions, to set name attributes

        # define correct choices (after calling secondary setup)
        xml = self.xml
        cxml = xml.xpath('//*[@id=$id]//choice[@correct="true"]',id=xml.get('id'))
        self.correct_choices = [choice.get('name') for choice in cxml]

    def mc_setup_response(self):
        '''
        Initialize name attributes in <choice> stanzas in the <choicegroup> in this response.
        '''
        i=0
        for response in self.xml.xpath("choicegroup"):
            rtype = response.get('type')
            if rtype not in ["MultipleChoice"]:
                response.set("type", "MultipleChoice")		# force choicegroup to be MultipleChoice if not valid
            for choice in list(response):
                if choice.get("name") is None:
                    choice.set("name", "choice_"+str(i))
                    i+=1
                else:
                    choice.set("name", "choice_"+choice.get("name"))

    def get_score(self, student_answers):
        '''
        grade student response.
        '''
        # log.debug('%s: student_answers=%s, correct_choices=%s' % (unicode(self),student_answers,self.correct_choices))
        if self.answer_id in student_answers and student_answers[self.answer_id] in self.correct_choices:
            return {self.answer_id:'correct'}
        else:
            return {self.answer_id:'incorrect'}

    def get_answers(self):
        return {self.answer_id:self.correct_choices}

class TrueFalseResponse(MultipleChoiceResponse):
    def mc_setup_response(self):
        i=0
        for response in self.xml.xpath("choicegroup"):
            response.set("type", "TrueFalse")
            for choice in list(response):
                if choice.get("name") is None:
                    choice.set("name", "choice_"+str(i))
                    i+=1
                else:
                    choice.set("name", "choice_"+choice.get("name"))
    
    def get_score(self, student_answers):
        correct = set(self.correct_choices)
        answers = set(student_answers.get(self.answer_id, []))
        
        if correct == answers:
            return { self.answer_id : 'correct'}
        
        return {self.answer_id : 'incorrect'}

#-----------------------------------------------------------------------------

class OptionResponse(GenericResponse):
    '''
    TODO: handle direction and randomize
    '''
    snippets = [{'snippet': '''<optionresponse direction="vertical" randomize="yes">
        <optioninput options="('Up','Down')" correct="Up"><text>The location of the sky</text></optioninput>
        <optioninput options="('Up','Down')" correct="Down"><text>The location of the earth</text></optioninput>
    </optionresponse>'''}]

    allowed_inputfields = ['optioninput']

    def setup_response(self):
        self.answer_fields = self.inputfields

    def get_score(self, student_answers):
        # log.debug('%s: student_answers=%s' % (unicode(self),student_answers))
        cmap = {}
        amap = self.get_answers()
        for aid in amap:
            if aid in student_answers and student_answers[aid]==amap[aid]:
                cmap[aid] = 'correct'
            else:
                cmap[aid] = 'incorrect'
        return cmap

    def get_answers(self):
        amap = dict([(af.get('id'),af.get('correct')) for af in self.answer_fields])
        # log.debug('%s: expected answers=%s' % (unicode(self),amap))
        return amap

#-----------------------------------------------------------------------------

class NumericalResponse(GenericResponse):

    allowed_inputfields = ['textline']
    required_attributes = ['answer']
    max_inputfields = 1

    def setup_response(self):
        xml = self.xml
        context = self.context
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        try:
            self.tolerance_xml = xml.xpath('//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                                           id=xml.get('id'))[0]
            self.tolerance = contextualize_text(self.tolerance_xml, context)
        except Exception:
            self.tolerance = 0
        try:
            self.answer_id = xml.xpath('//*[@id=$id]//textline/@id',
                                       id=xml.get('id'))[0]
        except Exception:
            self.answer_id = None

    def get_score(self, student_answers):
        '''Grade a numeric response '''
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
    Custom response.  The python code to be run should be in <answer>...</answer>
    or in a <script>...</script>
    '''
    snippets = [{'snippet': '''<customresponse>
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
    </customresponse>'''},
    {'snippet': '''<script type="loncapa/python"><![CDATA[

def sympy_check2():
  messages[0] = '%s:%s' % (submission[0],fromjs[0].replace('<','&lt;'))
  #messages[0] = str(answers)
  correct[0] = 'correct'

]]>
</script>

  <customresponse cfn="sympy_check2" type="cs" expect="2.27E-39" dojs="math" size="30" answer="2.27E-39">
    <textline size="40" dojs="math" />
    <responseparam description="Numerical Tolerance" type="tolerance" default="0.00001" name="tol"/>
  </customresponse>'''}]

    allowed_inputfields = ['textline','textbox']

    def setup_response(self):
        xml = self.xml
        context = self.context

        # if <customresponse> has an "expect" (or "answer") attribute then save that
        self.expect = xml.get('expect') or xml.get('answer')
        self.myid = xml.get('id')

        log.debug('answer_ids=%s' % self.answer_ids)

        # the <answer>...</answer> stanza should be local to the current <customresponse>.  So try looking there first.
        self.code = None
        answer = None
        try:
            answer = xml.xpath('//*[@id=$id]//answer',id=xml.get('id'))[0]
        except IndexError:
            # print "xml = ",etree.tostring(xml,pretty_print=True)

            # if we have a "cfn" attribute then look for the function specified by cfn, in the problem context
            # ie the comparison function is defined in the <script>...</script> stanza instead
            cfn = xml.get('cfn')
            if cfn:
                log.debug("cfn = %s" % cfn)
                if cfn in self.context:
                    self.code = self.context[cfn]
                else:
                    msg = "%s: can't find cfn in context = %s" % (unicode(self),self.context)
                    msg += "\nSee XML source line %s" % getattr(self.xml,'sourceline','<unavailable>')
                    raise LoncapaProblemError(msg)

        if not self.code:
            if answer is None:
                # raise Exception,"[courseware.capa.responsetypes.customresponse] missing code checking script! id=%s" % self.myid
                log.error("[courseware.capa.responsetypes.customresponse] missing code checking script! id=%s" % self.myid)
                self.code = ''
            else:
                answer_src = answer.get('src')
                if answer_src is not None:
                    self.code = self.system.filesystem.open('src/'+answer_src).read()
                else:
                    self.code = answer.text

    def get_score(self, student_answers):
        '''
        student_answers is a dict with everything from request.POST, but with the first part
        of each key removed (the string before the first "_").
        '''

        log.debug('%s: student_answers=%s' % (unicode(self),student_answers))

        idset = sorted(self.answer_ids)				# ordered list of answer id's
        try:
            submission = [student_answers[k] for k in idset]	# ordered list of answers
        except Exception, err:
            msg = '[courseware.capa.responsetypes.customresponse] error getting student answer from %s' % student_answers
            msg += '\n idset = %s, error = %s' % (idset,err)
            log.error(msg)
            raise Exception,msg

        # global variable in context which holds the Presentation MathML from dynamic math input
        dynamath = [ student_answers.get(k+'_dynamath',None) for k in idset ]	# ordered list of dynamath responses

        # if there is only one box, and it's empty, then don't evaluate
        if len(idset)==1 and not submission[0]:
            return {idset[0]:'no_answer_entered'}

        correct = ['unknown'] * len(idset)
        messages = [''] * len(idset)

        # put these in the context of the check function evaluator
        # note that this doesn't help the "cfn" version - only the exec version
        self.context.update({'xml' : self.xml,		# our subtree
                             'response_id' : self.myid,	# my ID
                             'expect': self.expect,		# expected answer (if given as attribute)
                             'submission':submission,		# ordered list of student answers from entry boxes in our subtree
                             'idset':idset,			# ordered list of ID's of all entry boxes in our subtree
                             'dynamath':dynamath,		# ordered list of all javascript inputs in our subtree
                             'answers':student_answers,		# dict of student's responses, with keys being entry box IDs
                             'correct':correct,			# the list to be filled in by the check function
                             'messages':messages,		# the list of messages to be filled in by the check function
                             'options':self.xml.get('options'),	# any options to be passed to the cfn
                             'testdat':'hello world',
                             })

        # pass self.system.debug to cfn 
        self.context['debug'] = self.system.DEBUG

        # exec the check function
        if type(self.code)==str:
            try:
                exec self.code in self.context['global_context'], self.context
            except Exception,err:
                print "oops in customresponse (code) error %s" % err
                print "context = ",self.context
                print traceback.format_exc()
        else:					# self.code is not a string; assume its a function

            # this is an interface to the Tutor2 check functions
            fn = self.code
            ret = None
            log.debug(" submission = %s" % submission)
            try:
                answer_given = submission[0] if (len(idset)==1) else submission
                # handle variable number of arguments in check function, for backwards compatibility
                # with various Tutor2 check functions
                args = [self.expect,answer_given,student_answers,self.answer_ids[0]]
                argspec = inspect.getargspec(fn)
                nargs = len(argspec.args)-len(argspec.defaults or [])
                kwargs = {}
                for argname in argspec.args[nargs:]:
                    kwargs[argname] = self.context[argname] if argname in self.context else None

                log.debug('[customresponse] answer_given=%s' % answer_given)
                log.debug('nargs=%d, args=%s, kwargs=%s' % (nargs,args,kwargs))

                ret = fn(*args[:nargs],**kwargs)
            except Exception,err:
                log.error("oops in customresponse (cfn) error %s" % err)
                # print "context = ",self.context
                log.error(traceback.format_exc())
                raise Exception,"oops in customresponse (cfn) error %s" % err
            log.debug("[courseware.capa.responsetypes.customresponse.get_score] ret = %s" % ret)
            if type(ret)==dict:
                correct = ['correct']*len(idset) if ret['ok'] else ['incorrect']*len(idset)
                msg = ret['msg']

                if 1:
                    # try to clean up message html
                    msg = '<html>'+msg+'</html>'
                    msg = msg.replace('&#60;','&lt;')
                    #msg = msg.replace('&lt;','<')
                    msg = etree.tostring(fromstring_bs(msg,convertEntities=None),pretty_print=True)
                    #msg = etree.tostring(fromstring_bs(msg),pretty_print=True)
                    msg = msg.replace('&#13;','')
                    #msg = re.sub('<html>(.*)</html>','\\1',msg,flags=re.M|re.DOTALL)	# python 2.7
                    msg = re.sub('(?ms)<html>(.*)</html>','\\1',msg)

                messages[0] = msg
            else:
                correct = ['correct']*len(idset) if ret else ['incorrect']*len(idset)

        # build map giving "correct"ness of the answer(s)
        #correct_map = dict(zip(idset, self.context['correct']))
        correct_map = {}
        for k in range(len(idset)):
            correct_map[idset[k]] = correct[k]
            correct_map['msg_%s' % idset[k]] = messages[k]
        return  correct_map

    def get_answers(self):
        '''
        Give correct answer expected for this response.

        use default_answer_map from entry elements (eg textline),
        when this response has multiple entry objects.

        but for simplicity, if an "expect" attribute was given by the content author
        ie <customresponse expect="foo" ...> then that.
        '''
        if len(self.answer_ids)>1:
            return self.default_answer_map
        if self.expect:
            return {self.answer_ids[0] : self.expect}
        return self.default_answer_map

#-----------------------------------------------------------------------------

class SymbolicResponse(CustomResponse):
    """
    Symbolic math response checking, using symmath library.
    """
    snippets = [{'snippet': '''<problem>
      <text>Compute \[ \exp\left(-i \frac{\theta}{2} \left[ \begin{matrix} 0 & 1 \\ 1 & 0 \end{matrix} \right] \right) \]
      and give the resulting \(2\times 2\) matrix: <br/>
        <symbolicresponse answer="">
          <textline size="40" math="1" />
        </symbolicresponse>
      <br/>
      Your input should be typed in as a list of lists, eg <tt>[[1,2],[3,4]]</tt>.
      </text>
    </problem>'''}]

    def setup_response(self):
        self.xml.set('cfn','symmath_check')
        code = "from symmath import *"
        exec code in self.context,self.context
        CustomResponse.setup_response(self)

#-----------------------------------------------------------------------------

class ExternalResponse(GenericResponse):
    '''
    Grade the students input using an external server.
    
    Typically used by coding problems.

    '''
    snippets = [{'snippet': '''<externalresponse tests="repeat:10,generate">
    <textbox rows="10" cols="70"  mode="python"/>
    <answer><![CDATA[
initial_display = """
def inc(x):
"""

answer = """
def inc(n):
    return n+1
"""
preamble = """ 
import sympy
"""
test_program = """
import random

def testInc(n = None):
    if n is None:
       n = random.randint(2, 20)
    print 'Test is: inc(%d)'%n
    return str(inc(n))

def main():
   f = os.fdopen(3,'w')
   test = int(sys.argv[1])
   rndlist = map(int,os.getenv('rndlist').split(','))
   random.seed(rndlist[0])
   if test == 1: f.write(testInc(0))
   elif test == 2: f.write(testInc(1))
   else:  f.write(testInc())
   f.close()

main()
"""
]]>
    </answer>
  </externalresponse>'''}]

    allowed_inputfields = ['textline','textbox']

    def setup_response(self):
        xml = self.xml
        self.url = xml.get('url') or "http://eecs1.mit.edu:8889/pyloncapa"	# FIXME - hardcoded URL

        answer = xml.xpath('//*[@id=$id]//answer',id=xml.get('id'))[0]	# FIXME - catch errors
        answer_src = answer.get('src')
        if answer_src is not None:
            self.code = self.system.filesystem.open('src/'+answer_src).read()
        else:
            self.code = answer.text

        self.tests = xml.get('tests')

    def do_external_request(self,cmd,extra_payload):
        '''
        Perform HTTP request / post to external server.

        cmd = remote command to perform (str)
        extra_payload = dict of extra stuff to post.

        Return XML tree of response (from response body)
        '''
        xmlstr = etree.tostring(self.xml, pretty_print=True)
        payload = {'xml': xmlstr, 
                   'edX_cmd' : cmd,
                   'edX_tests': self.tests,
                   'processor' : self.code,
                   }
        payload.update(extra_payload)

        try:
            r = requests.post(self.url,data=payload)          # call external server
        except Exception,err:
            msg = 'Error %s - cannot connect to external server url=%s' % (err,self.url)
            log.error(msg)
            raise Exception, msg

        if self.system.DEBUG: log.info('response = %s' % r.text)

        if (not r.text ) or (not r.text.strip()):
            raise Exception,'Error: no response from external server url=%s' % self.url

        try:
            rxml = etree.fromstring(r.text)         # response is XML; prase it
        except Exception,err:
            msg = 'Error %s - cannot parse response from external server r.text=%s' % (err,r.text)
            log.error(msg)
            raise Exception, msg

        return rxml

    def get_score(self, student_answers):
        try:
            submission = [student_answers[k] for k in sorted(self.answer_ids)]
        except Exception,err:
            log.error('Error %s: cannot get student answer for %s; student_answers=%s' % (err,self.answer_ids,student_answers))
            raise Exception,err

        self.context.update({'submission':submission})

        extra_payload = {'edX_student_response': json.dumps(submission)}

        try:
            rxml = self.do_external_request('get_score',extra_payload)
        except Exception, err:
            log.error('Error %s' % err)
            if self.system.DEBUG:
                correct_map = dict(zip(sorted(self.answer_ids), ['incorrect'] * len(self.answer_ids) ))
                correct_map['msg_%s' % self.answer_ids[0]] = '<font color="red" size="+2">%s</font>' % str(err).replace('<','&lt;')
                return correct_map

        ad = rxml.find('awarddetail').text
        admap = {'EXACT_ANS':'correct',         # TODO: handle other loncapa responses
        	 'WRONG_FORMAT': 'incorrect',
                 }
        self.context['correct'] = ['correct']
        if ad in admap:
            self.context['correct'][0] = admap[ad]

        # self.context['correct'] = ['correct','correct']
        correct_map = dict(zip(sorted(self.answer_ids), self.context['correct']))
        
        # store message in correct_map
        correct_map['msg_%s' % self.answer_ids[0]] = rxml.find('message').text.replace('&nbsp;','&#160;')  

        return  correct_map

    def get_answers(self):
        '''
        Use external server to get expected answers
        '''
        try:
            rxml = self.do_external_request('get_answers',{})
            exans = json.loads(rxml.find('expected').text)
        except Exception,err:
            log.error('Error %s' % err)
            if self.system.DEBUG:
                msg = '<font color=red size=+2>%s</font>' % str(err).replace('<','&lt;')
                exans = [''] * len(self.answer_ids)
                exans[0] = msg
            
        if not (len(exans)==len(self.answer_ids)):
            log.error('Expected %d answers from external server, only got %d!' % (len(self.answer_ids),len(exans)))
            raise Exception,'Short response from external server'
        return dict(zip(self.answer_ids,exans))


#-----------------------------------------------------------------------------

class FormulaResponse(GenericResponse):
    '''
    Checking of symbolic math response using numerical sampling.
    '''
    snippets = [{'snippet': '''<problem>

    <script type="loncapa/python">
    I = "m*c^2"
    </script>

    <text>
    <br/>
    Give an equation for the relativistic energy of an object with mass m.
    </text>
    <formularesponse type="cs" samples="m,c@1,2:3,4#10" answer="$I">
      <responseparam description="Numerical Tolerance" type="tolerance"
                   default="0.00001" name="tol" /> 
      <textline size="40" math="1" />    
    </formularesponse>

    </problem>'''}]

    allowed_inputfields = ['textline']
    required_attributes = ['answer']
    max_inputfields = 1

    def setup_response(self):
        xml = self.xml
        context = self.context
        self.correct_answer = contextualize_text(xml.get('answer'), context)
        self.samples = contextualize_text(xml.get('samples'), context)
        try:
            self.tolerance_xml = xml.xpath('//*[@id=$id]//responseparam[@type="tolerance"]/@default',
                                           id=xml.get('id'))[0]
            self.tolerance = contextualize_text(self.tolerance_xml, context)
        except Exception:
            self.tolerance = 0

        ts = xml.get('type')
        if ts is None:
            typeslist = []
        else:
            typeslist = ts.split(',')
        if 'ci' in typeslist: # Case insensitive
            self.case_sensitive = False
        elif 'cs' in typeslist: # Case sensitive
            self.case_sensitive = True
        else: # Default
            self.case_sensitive = False

    def get_score(self, student_answers):
        variables=self.samples.split('@')[0].split(',')
        numsamples=int(self.samples.split('@')[1].split('#')[1])
        sranges=zip(*map(lambda x:map(float, x.split(",")), 
                         self.samples.split('@')[1].split('#')[0].split(':')))

        ranges=dict(zip(variables, sranges))
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

    allowed_inputfields = ['schematic']

    def setup_response(self):
        xml = self.xml
        answer = xml.xpath('//*[@id=$id]//answer', id=xml.get('id'))[0]
        answer_src = answer.get('src')
        if answer_src is not None:
            self.code = self.system.filestore.open('src/'+answer_src).read() # Untested; never used
        else:
            self.code = answer.text

    def get_score(self, student_answers):
        from capa_problem import global_context
        submission = [json.loads(student_answers[k]) for k in sorted(self.answer_ids)]
        self.context.update({'submission':submission})
        exec self.code in global_context, self.context
        return  zip(sorted(self.answer_ids), self.context['correct'])

    def get_answers(self):
        # use answers provided in input elements
        return self.default_answer_map

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
    """
    snippets = [{'snippet': '''<imageresponse>
      <imageinput src="image1.jpg" width="200" height="100" rectangle="(10,10)-(20,30)" />
      <imageinput src="image2.jpg" width="210" height="130" rectangle="(12,12)-(40,60)" />
    </imageresponse>'''}]

    allowed_inputfields = ['imageinput']

    def setup_response(self):
        self.ielements = self.inputfields
        self.answer_ids = [ie.get('id')  for ie in self.ielements]

    def get_score(self, student_answers):
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
                raise Exception,'[capamodule.capa.responsetypes.imageinput] error grading %s (input=%s)' % (aid,given)
            (gx,gy) = [int(x) for x in m.groups()]
            
            # answer is correct if (x,y) is within the specified rectangle
            if (llx <= gx <= urx) and (lly <= gy <= ury):
                correct_map[aid] = 'correct'
            else:
                correct_map[aid] = 'incorrect'
        return correct_map

    def get_answers(self):
        return dict([(ie.get('id'),ie.get('rectangle')) for ie in self.ielements])
