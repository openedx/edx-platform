# For calculator: 
# http://pyparsing.wikispaces.com/file/view/fourFn.py

import random, numpy, math, scipy, sys, StringIO, os, struct, json
from x_module import XModule

from capa_problem import LoncapaProblem

import dateutil
import datetime


from xml.dom.minidom import parse, parseString

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

    attempts = None
    max_attempts = None

    due_date = None

    def get_state(self):
        return self.lcp.get_state()

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
        closed = False
        if self.lcp.done:
            check_button="Reset"
        else:
            check_button="Check"
        html=render_to_string('problem.html', 
                              {'problem':content, 
                               'id':self.filename, 
                               'check_button':check_button,
                               'ajax_url':self.ajax_url,
                               })
        if encapsulate:
            html = '<div id="main_{id}">'.format(id=self.item_id)+html+"</div>"
            
        return html

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state)
        dom=parseString(xml)
        node=dom.childNodes[0]

        self.due_date=node.getAttribute("due")
        if len(self.due_date)>0:
            self.due_date=dateutil.parser.parse(self.due_date)
        else:
            self.due_date=None
            
        self.max_attempts=node.getAttribute("attempts")
        if len(self.max_attempts)>0:
            self.max_attempts=int(self.max_attempts)
        else:
            self.max_attempts=None

        self.filename=node.getAttribute("filename")
        filename=settings.DATA_DIR+self.filename+".xml"
        self.name=node.getAttribute("name")
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
        else: 
            return "Error"
        return response


    # Figure out if we should move these to capa_problem?
    def get_problem(self, get):
        ''' Same as get_problem_html -- if we want to reconfirm we have the right 
            thing e.g. after several AJAX calls. '''
        return self.get_problem_html(encapsulate=False)        

    def check_problem(self, get):
        ''' Checks whether answers to a problem are correct, and returns
            a map of correct/incorrect answers '''
        self.lcp.done=True
        answer=dict()
        # input_resistor_1 ==> resistor_1
        for key in get:
            answer['_'.join(key.split('_')[1:])]=get[key]

        js=json.dumps(self.lcp.grade_answers(answer))

        return js

    def reset_problem(self, get):
        ''' Changes problem state to unfinished -- removes student answers, 
            and causes problem to rerender itself. '''
        self.lcp.done=False
        self.lcp.answers=dict()
        self.lcp.context=dict()
        self.lcp.questions=dict() # Detailed info about questions in problem instance. TODO: Should be by id and not lid. 
        self.lcp.answers=dict()   # Student answers
        self.lcp.correct_map=dict()
        self.lcp.seed=None
        filename=settings.DATA_DIR+self.filename+".xml"
        self.lcp=LoncapaProblem(filename, self.item_id, self.lcp.get_state())
        return json.dumps(self.get_problem_html(encapsulate=False))
