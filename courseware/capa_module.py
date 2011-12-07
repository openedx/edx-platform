# For calculator: 
# http://pyparsing.wikispaces.com/file/view/fourFn.py

import random, numpy, math, scipy, sys, StringIO, os, struct, json
from x_module import XModule

from xml.dom.minidom import parse, parseString

class LoncapaProblem(XModule):
    def get_state(self):

    def get_score(self):

    def max_score(self):

    def get_html(self):

    def handle_ajax(self, json):

    def __init__(self, filename, id=None, state=None):


if __name__=='__main__':  
    p=LoncapaProblem('<problem name="Problem 1: Resistive Divider" filename="resistor" />')

    print p.getHtml()
    print p.getContext()
    print p.getSeed()
 # Chef and puppot
