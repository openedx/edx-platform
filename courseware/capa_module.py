import random, numpy, math, scipy, sys, StringIO, os, struct, json
from x_module import XModule

from capa_problem import LoncapaProblem
from django.http import Http404

import dateutil
import datetime

import content_parser

from lxml import etree

## TODO: Abstract out from Django
from django.conf import settings
from djangomako.shortcuts import render_to_response, render_to_string

class LoncapaModule(XModule):
    ''' Interface between capa_problem and x_module. Originally a hack
    meant to be refactored out, but it seems to be serving a useful
    prupose now. We can e.g .destroy and create the capa_problem on a
    reset. 
    '''
    xml_tags = ["problem"]
    id_attribute = "filename"


    def get_state(self):
        state = self.lcp.get_state()
        state['attempts'] = self.attempts
        return json.dumps(state)

    def get_score(self):
        return self.lcp.get_score()

    def max_score(self):
        return len(self.lcp.questions)

    def get_html(self):
        return render_to_string('problem_ajax.html', 
                              {'id':self.filename, 
                               'ajax_url':self.ajax_url,
                               })

    def get_init_js(self):
        return render_to_string('problem.js', 
                              {'id':self.filename, 
                               'ajax_url':self.ajax_url,
                               })

    def get_problem_html(self, encapsulate=True):
        html = self.lcp.get_html()
        content={'name':self.name, 
                 'html':html}
        
        check_button = True
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
        if self.lcp.done and self.rerandomize:
            #print "!"
            check_button = False
            save_button = False
        
        # User hasn't submitted an answer yet -- we don't want resets
        if not self.lcp.done:
            reset_button = False

        attempts_str = ""
        if self.max_attempts != None: 
            attempts_str = " ({a}/{m})".format(a=self.attempts, m=self.max_attempts)

        html=render_to_string('problem.html', 
                              {'problem' : content, 
                               'id' : self.filename, 
                               'check_button' : check_button,
                               'reset_button' : reset_button,
                               'save_button' : save_button,
                               'answer_available' : self.answer_available(),
                               'ajax_url' : self.ajax_url,
                               'attempts': attempts_str
                               })
        if encapsulate:
            html = '<div id="main_{id}">'.format(id=self.item_id)+html+"</div>"
            
        return html

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state)

        self.attempts = 0
        self.max_attempts = None
        self.due_date = None

        #dom=parseString(xml)
        #dom2 = libxml2.parseMemory(xml, len(xml))
        dom2 = etree.fromstring(xml)

        #node=dom.childNodes[0]

        #self.due_date=node.getAttribute("due")
        self.due_date=content_parser.item(dom2.xpath('/problem/@due'))#dom2.xpathEval('/problem/@due'))
        if len(self.due_date)>0:
            self.due_date=dateutil.parser.parse(self.due_date)
        else:
            self.due_date=None
            
        #self.max_attempts=node.getAttribute("attempts")
        self.max_attempts=content_parser.item(dom2.xpath('/problem/@attempts'))
        if len(self.max_attempts)>0:
            self.max_attempts=int(self.max_attempts)
        else:
            self.max_attempts=None

        #self.show_answer=node.getAttribute("showanswer")
        self.show_answer=content_parser.item(dom2.xpath('/problem/@showanswer'))

        if self.show_answer=="":
            self.show_answer="closed"

        self.rerandomize=content_parser.item(dom2.xpath('/problem/@rerandomize'))
        #self.rerandomize=node.getAttribute("rerandomize")
        if self.rerandomize=="":
            self.rerandomize=True
        elif self.rerandomize=="false":
            self.rerandomize=False
        elif self.rerandomize=="true":
            self.rerandomize=True
        else:
            raise Exception("Invalid rerandomize attribute "+self.rerandomize)

        if state!=None:
            state=json.loads(state)
        if state!=None and 'attempts' in state:
            self.attempts=state['attempts']

        self.filename=content_parser.item(dom2.xpath('/problem/@filename'))
        #self.filename=node.getAttribute("filename")
        #print self.filename
        filename=settings.DATA_DIR+"problems/"+self.filename+".xml"
        #self.name=node.getAttribute("name")
        self.name=content_parser.item(dom2.xpath('/problem/@name'))
        self.lcp=LoncapaProblem(filename, self.item_id, state)

    def handle_ajax(self, dispatch, get):
        if dispatch=='problem_get':
            response = self.get_problem(get)
        elif False: #self.due_date > 
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
        if self.due_date != None and datetime.datetime.utcnow() > self.due_date:
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
        print "aa", self.show_answer
        raise Http404

    def get_answer(self, get):
        if not self.answer_available():
            raise Http404
        else: 
            return json.dumps(self.lcp.get_question_answers())


    # Figure out if we should move these to capa_problem?
    def get_problem(self, get):
        ''' Same as get_problem_html -- if we want to reconfirm we
            have the right thing e.g. after several AJAX calls.'''
        return self.get_problem_html(encapsulate=False)        

    def check_problem(self, get):
        ''' Checks whether answers to a problem are correct, and
            returns a map of correct/incorrect answers'''
        # Too late. Cannot submit
        if self.closed():
            print "cp"
            raise Http404
            
        # Problem submitted. Student should reset before checking
        # again.
        if self.lcp.done and self.rerandomize:
            print "cpdr"
            raise Http404

        self.attempts = self.attempts + 1
        self.lcp.done=True
        answers=dict()
        # input_resistor_1 ==> resistor_1
        for key in get:
            answers['_'.join(key.split('_')[1:])]=get[key]

        correct_map = self.lcp.grade_answers(answers)

        success = True
        for i in correct_map:
            if correct_map[i]!='correct':
                success = False

        js=json.dumps({'correct_map' : correct_map,
                       'success' : success})

        return js

    def save_problem(self, get):
        # Too late. Cannot submit
        if self.closed():
            print "sp"
            return "Problem is closed"
            
        # Problem submitted. Student should reset before saving
        # again.
        if self.lcp.done and self.rerandomize:
            print "spdr"
            return "Problem needs to be reset prior to save."

        answers=dict()
        for key in get:
            answers['_'.join(key.split('_')[1:])]=get[key]
        
        self.lcp.answers=answers

        return json.dumps({'success':True})

    def reset_problem(self, get):
        ''' Changes problem state to unfinished -- removes student answers, 
            and causes problem to rerender itself. '''
        if self.closed():
            return "Problem is closed"
            
        if not self.lcp.done:
            return "Refresh the page and make an attempt before resetting."

        self.lcp.done=False
        self.lcp.answers=dict()
        self.lcp.correct_map=dict()

        if self.rerandomize:
            self.lcp.context=dict()
            self.lcp.questions=dict() # Detailed info about questions in problem instance. TODO: Should be by id and not lid. 
            self.lcp.seed=None

        filename=settings.DATA_DIR+"problems/"+self.filename+".xml"
        self.lcp=LoncapaProblem(filename, self.item_id, self.lcp.get_state())
        return json.dumps(self.get_problem_html(encapsulate=False))
