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
        print "got"
        return self.lcp.get_state()

    def get_score(self):
        return self.lcp.get_score()

    def max_score(self):
        return len(lcp.questions)

    def get_html(self):
        inner_html=self.lcp.get_html()
        content={'name':self.name, 
                 'html':inner_html}
        return render_to_string('problem.html', 
                                {'problem':content, 'id':self.filename})



    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state)
        dom=parseString(xml)
        node=dom.childNodes[0]
        self.filename=node.getAttribute("filename")
        filename=settings.DATA_DIR+self.filename+".xml"
        self.name=node.getAttribute("name")
        print state
        self.lcp=LoncapaProblem(filename, item_id, state)

    # Temporary

    def check_problem(self, get):
        pass
