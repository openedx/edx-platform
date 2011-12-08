# For calculator: 
# http://pyparsing.wikispaces.com/file/view/fourFn.py

import random, numpy, math, scipy, sys, StringIO, os, struct, json
from x_module import XModule

from capa_problem import LoncapaProblem

from xml.dom.minidom import parse, parseString

## TODO: Abstract out from Django
from django.conf import settings
from djangomako.shortcuts import render_to_response, render_to_string

class LoncapaModule(XModule):
    xml_tags=["problem"]
    id_attribute="filename"

    def get_state(self):
        return self.lcp.get_state()

    def get_score(self):
        return self.lcp.get_score()

    def max_score(self):
        return len(lcp.questions)

    def get_html(self):
        inner_html=self.lcp.get_html()
        content={'name':self.name, 
                 'html':inner_html}
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
        print self.lcp.done
        return render_to_string('problem.html', 
                                {'problem':content, 'id':self.filename, 'done':self.lcp.done})

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state)
        dom=parseString(xml)
        node=dom.childNodes[0]
        self.filename=node.getAttribute("filename")
        filename=settings.DATA_DIR+self.filename+".xml"
        self.name=node.getAttribute("name")
        self.lcp=LoncapaProblem(filename, item_id, state)

    def handle_ajax(self, dispatch, get):
        if dispatch=='problem_check': 
            html = self.check_problem(get)
        elif dispatch=='problem_reset':
            html = self.reset_problem(get)
        else: 
            return "Error"
        return html


    # Temporary -- move to capa_problem

    def check_problem(self, get):
        self.lcp.done=True
        answer=dict()
        # input_resistor_1 ==> resistor_1
        for key in get:
            answer['_'.join(key.split('_')[1:])]=get[key]

        js=json.dumps(self.lcp.grade_answers(answer))

        return js

    def reset_problem(self, get):
        self.lcp.done=False
        self.lcp.answers=dict()
        self.lcp.context=dict()
        self.lcp.questions=dict() # Detailed info about questions in problem instance. TODO: Should be by id and not lid. 
        self.lcp.answers=dict()   # Student answers
        self.lcp.correct_map=dict()
        self.lcp.seed=None
        return "{}"
