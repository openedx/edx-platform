import StringIO
import datetime
import dateutil
import dateutil.parser
import json
import logging
import math
import numpy
import os
import random
import scipy
import struct
import sys
import traceback

from lxml import etree

## TODO: Abstract out from Django
from mitxmako.shortcuts import render_to_string

from x_module import XModule
from courseware.capa.capa_problem import LoncapaProblem, StudentInputError
import courseware.content_parser as content_parser
from multicourse import multicourse_settings

log = logging.getLogger("mitx.courseware")

#-----------------------------------------------------------------------------

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, complex):
            return "{real:.7g}{imag:+.7g}*j".format(real = obj.real,imag = obj.imag)
        return json.JSONEncoder.default(self, obj)

class Module(XModule):
    ''' Interface between capa_problem and x_module. Originally a hack
    meant to be refactored out, but it seems to be serving a useful
    prupose now. We can e.g .destroy and create the capa_problem on a
    reset. 
    '''

    id_attribute = "filename"

    @classmethod
    def get_xml_tags(c):
        return ["problem"]

    def get_state(self):
        state = self.lcp.get_state()
        state['attempts'] = self.attempts
        return json.dumps(state)

    def get_score(self):
        return self.lcp.get_score()

    def max_score(self):
        return self.lcp.get_max_score()

    def get_html(self):
        return render_to_string('problem_ajax.html', 
                              {'id':self.item_id, 
                               'ajax_url':self.ajax_url,
                               })

    def get_init_js(self):
        return render_to_string('problem.js', 
                              {'id':self.item_id, 
                               'ajax_url':self.ajax_url,
                               })

    def get_problem_html(self, encapsulate=True):
        html = self.lcp.get_html()
        content={'name':self.name, 
                 'html':html, 
                 'weight': self.weight,
                 }
        
        # We using strings as truthy values, because the terminology of the check button
        # is context-specific.
        check_button = "Grade" if self.max_attempts else "Check"
        reset_button = True
        save_button = True

        # If we're after deadline, or user has exhuasted attempts, 
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
        if self.rerandomize != 'always':
            reset_button = False

        # User hasn't submitted an answer yet -- we don't want resets
        if not self.lcp.done:
            reset_button = False

        # We don't need a "save" button if infinite number of attempts and non-randomized
        if self.max_attempts == None and self.rerandomize != "always":
            save_button = False

        # Check if explanation is available, and if so, give a link
        explain=""
        if self.lcp.done and self.explain_available=='attempted':
            explain=self.explanation
        if self.closed() and self.explain_available=='closed':
            explain=self.explanation
        
        if len(explain) == 0:
            explain = False

        context = {'problem' : content, 
                   'id' : self.item_id, 
                   'check_button' : check_button,
                   'reset_button' : reset_button,
                   'save_button' : save_button,
                   'answer_available' : self.answer_available(),
                   'ajax_url' : self.ajax_url,
                   'attempts_used': self.attempts, 
                   'attempts_allowed': self.max_attempts, 
                   'explain': explain,
                   }

        html=render_to_string('problem.html', context)
        if encapsulate:
            html = '<div id="main_{id}">'.format(id=self.item_id)+html+"</div>"
            
        return html

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)

        self.attempts = 0
        self.max_attempts = None
        
        dom2 = etree.fromstring(xml)
        
        self.explanation="problems/"+content_parser.item(dom2.xpath('/problem/@explain'), default="closed")
        # TODO: Should be converted to: self.explanation=content_parser.item(dom2.xpath('/problem/@explain'), default="closed")
        self.explain_available=content_parser.item(dom2.xpath('/problem/@explain_available'))

        display_due_date_string=content_parser.item(dom2.xpath('/problem/@due'))
        if len(display_due_date_string)>0:
            self.display_due_date=dateutil.parser.parse(display_due_date_string)
            #log.debug("Parsed " + display_due_date_string + " to " + str(self.display_due_date))
        else:
            self.display_due_date=None
        
        
        grace_period_string = content_parser.item(dom2.xpath('/problem/@graceperiod'))
        if len(grace_period_string)>0 and self.display_due_date:
            self.grace_period = content_parser.parse_timedelta(grace_period_string)
            self.close_date = self.display_due_date + self.grace_period
            #log.debug("Then parsed " + grace_period_string + " to closing date" + str(self.close_date))
        else:
            self.grace_period = None
            self.close_date = self.display_due_date
            
        self.max_attempts=content_parser.item(dom2.xpath('/problem/@attempts'))
        if len(self.max_attempts)>0:
            self.max_attempts=int(self.max_attempts)
        else:
            self.max_attempts=None

        self.show_answer=content_parser.item(dom2.xpath('/problem/@showanswer'))

        if self.show_answer=="":
            self.show_answer="closed"

        self.rerandomize=content_parser.item(dom2.xpath('/problem/@rerandomize'))
        if self.rerandomize=="" or self.rerandomize=="always" or self.rerandomize=="true":
            self.rerandomize="always"
        elif self.rerandomize=="false" or self.rerandomize=="per_student":
            self.rerandomize="per_student"
        elif self.rerandomize=="never":
            self.rerandomize="never"
        else:
            raise Exception("Invalid rerandomize attribute "+self.rerandomize)

        if state!=None:
            state=json.loads(state)
        if state!=None and 'attempts' in state:
            self.attempts=state['attempts']

        # TODO: Should be: self.filename=content_parser.item(dom2.xpath('/problem/@filename')) 
        self.filename= "problems/"+content_parser.item(dom2.xpath('/problem/@filename'))+".xml"
        self.name=content_parser.item(dom2.xpath('/problem/@name'))
        self.weight=content_parser.item(dom2.xpath('/problem/@weight'))
        if self.rerandomize == 'never':
            seed = 1
        else:
            seed = None
        try:
            fp = self.filestore.open(self.filename)
        except Exception,err:
            print '[courseware.capa.capa_module.Module.init] error %s: cannot open file %s' % (err,self.filename)
            if self.DEBUG:
                # create a dummy problem instead of failing
                fp = StringIO.StringIO('<problem><text>Problem file %s is missing</text></problem>' % self.filename)
            else:
                raise Exception,err
        self.lcp=LoncapaProblem(fp, self.item_id, state, seed = seed, system=self.system)

    def handle_ajax(self, dispatch, get):
        '''
        This is called by courseware.module_render, to handle an AJAX call.  "get" is request.POST 
        '''
        if dispatch=='problem_get':
            response = self.get_problem(get)
        elif False: #self.close_date > 
            return json.dumps({"error":"Past due date"})
        elif dispatch=='problem_check': 
            response = self.check_problem(get)
        elif dispatch=='problem_reset':
            response = self.reset_problem(get)
        elif dispatch=='problem_save':
            response = self.save_problem(get)
        elif dispatch=='problem_show':
            response = self.get_answer(get)
        else: 
            return "Error"
        return response

    def closed(self):
        ''' Is the student still allowed to submit answers? '''
        if self.attempts == self.max_attempts:
            return True
        if self.close_date != None and datetime.datetime.utcnow() > self.close_date:
            return True

        return False
        

    def answer_available(self):
        ''' Is the user allowed to see an answer? 
        ''' 
        if self.show_answer == '':
            return False
        if self.show_answer == "never":
            return False
        if self.show_answer == 'attempted' and self.attempts == 0:
            return False
        if self.show_answer == 'attempted' and self.attempts > 0:
            return True
        if self.show_answer == 'answered' and self.lcp.done:
            return True
        if self.show_answer == 'answered' and not self.lcp.done:
            return False
        if self.show_answer == 'closed' and self.closed():
            return True
        if self.show_answer == 'closed' and not self.closed():
            return False
        if self.show_answer == 'always':
            return True
        raise self.system.exception404 #TODO: Not 404

    def get_answer(self, get):
        '''
        For the "show answer" button.

        TODO: show answer events should be logged here, not just in the problem.js
        '''
        if not self.answer_available():
            raise self.system.exception404
        else: 
            answers = self.lcp.get_question_answers()
            return json.dumps(answers, 
                              cls=ComplexEncoder)

    # Figure out if we should move these to capa_problem?
    def get_problem(self, get):
        ''' Same as get_problem_html -- if we want to reconfirm we
            have the right thing e.g. after several AJAX calls.'''
        return self.get_problem_html(encapsulate=False)        

    def check_problem(self, get):
        ''' Checks whether answers to a problem are correct, and
            returns a map of correct/incorrect answers'''
        event_info = dict()
        event_info['state'] = self.lcp.get_state()
        event_info['filename'] = self.filename

        # make a dict of all the student responses ("answers").
        answers=dict()
        # input_resistor_1 ==> resistor_1
        for key in get:
            answers['_'.join(key.split('_')[1:])]=get[key]

        event_info['answers']=answers

        # Too late. Cannot submit
        if self.closed():
            event_info['failure']='closed'
            self.tracker('save_problem_check_fail', event_info)
            raise self.system.exception404
            
        # Problem submitted. Student should reset before checking
        # again.
        if self.lcp.done and self.rerandomize == "always":
            event_info['failure']='unreset'
            self.tracker('save_problem_check_fail', event_info)
            raise self.system.exception404

        try:
            old_state = self.lcp.get_state()
            lcp_id = self.lcp.problem_id
            correct_map = self.lcp.grade_answers(answers)
        except StudentInputError as inst: 
            self.lcp = LoncapaProblem(self.filestore.open(self.filename), id=lcp_id, state=old_state, system=self.system)
            traceback.print_exc()
            return json.dumps({'success':inst.message})
        except: 
            self.lcp = LoncapaProblem(self.filestore.open(self.filename), id=lcp_id, state=old_state, system=self.system)
            traceback.print_exc()
            raise Exception,"error in capa_module"
            return json.dumps({'success':'Unknown Error'})
            
        self.attempts = self.attempts + 1
        self.lcp.done=True
        
        success = 'correct'
        for i in correct_map:
            if correct_map[i]!='correct':
                success = 'incorrect'

        event_info['correct_map']=correct_map
        event_info['success']=success

        self.tracker('save_problem_check', event_info)

        return json.dumps({'success': success,
                           'contents': self.get_problem_html(encapsulate=False)})

    def save_problem(self, get):
        event_info = dict()
        event_info['state'] = self.lcp.get_state()
        event_info['filename'] = self.filename

        answers=dict()
        for key in get:
            answers['_'.join(key.split('_')[1:])]=get[key]
        event_info['answers'] = answers

        # Too late. Cannot submit
        if self.closed():
            event_info['failure']='closed'
            self.tracker('save_problem_fail', event_info)
            return "Problem is closed"
            
        # Problem submitted. Student should reset before saving
        # again.
        if self.lcp.done and self.rerandomize == "always":
            event_info['failure']='done'
            self.tracker('save_problem_fail', event_info)
            return "Problem needs to be reset prior to save."

        self.lcp.student_answers=answers

        self.tracker('save_problem_fail', event_info)
        return json.dumps({'success':True})

    def reset_problem(self, get):
        ''' Changes problem state to unfinished -- removes student answers, 
            and causes problem to rerender itself. '''
        event_info = dict()
        event_info['old_state']=self.lcp.get_state()
        event_info['filename']=self.filename

        if self.closed():
            event_info['failure']='closed'
            self.tracker('reset_problem_fail', event_info)
            return "Problem is closed"
            
        if not self.lcp.done:
            event_info['failure']='not_done'
            self.tracker('reset_problem_fail', event_info)
            return "Refresh the page and make an attempt before resetting."

        self.lcp.done=False
        self.lcp.answers=dict()
        self.lcp.correct_map=dict()
        self.lcp.student_answers = dict()


        if self.rerandomize == "always":
            self.lcp.context=dict()
            self.lcp.questions=dict() # Detailed info about questions in problem instance. TODO: Should be by id and not lid. 
            self.lcp.seed=None

        self.lcp=LoncapaProblem(self.filestore.open(self.filename), self.item_id, self.lcp.get_state(), system=self.system)

        event_info['new_state']=self.lcp.get_state()
        self.tracker('reset_problem', event_info)

        return json.dumps(self.get_problem_html(encapsulate=False))
