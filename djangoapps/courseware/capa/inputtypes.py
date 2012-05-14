#
# File:   courseware/capa/inputtypes.py
#

'''
Module containing the problem elements which render into input objects

- textline
- textbox (change this to textarea?)
- schemmatic

These are matched by *.html files templates/*.html which are mako templates with the actual html.

'''

# TODO: rename "state" to "status" for all below
# status is currently the answer for the problem ID for the input element,
# but it will turn into a dict containing both the answer and any associated message for the problem ID for the input element.

import re

from django.conf import settings

from lxml.etree import Element
from lxml import etree

from mitxmako.shortcuts import render_to_string

#-----------------------------------------------------------------------------
#takes the xml tree as 'element', the student's previous answer as 'value', and the graded status as 'state'

def choicegroup(element, value, state, msg=""):
    '''
    Radio button inputs: multiple choice or true/false

    TODO: allow order of choices to be randomized, following lon-capa spec.  Use "location" attribute,
    ie random, top, bottom.
    '''
    eid=element.get('id')
    if element.get('type') == "MultipleChoice":
        type="radio"
    elif element.get('type') == "TrueFalse":
        type="checkbox"
    else:
        type="radio"
    choices={}
    for choice in element:
        assert choice.tag =="choice", "only <choice> tags should be immediate children of a <choicegroup>"
        choices[choice.get("name")] = etree.tostring(choice[0])	# TODO: what if choice[0] has math tags in it?
    context={'id':eid, 'value':value, 'state':state, 'type':type, 'choices':choices}
    html=render_to_string("choicegroup.html", context)
    return etree.XML(html)

def textline(element, value, state, msg=""):
    return TextLine(element, value, state, msg).render()

class GenericInput(object):
    def __init__(element, value, state, msg=""):
        ''' This will move into the parent object '''
        self.element = element
        self.value = value
        self.state = state
        self.msg = msg

class TextLine(GenericInput):
    def render(self):
        eid=self.element.get('id')
        count = int(eid.split('_')[-2])-1 # HACK
        size = self.element.get('size')
        context = {'id':eid, 'value':self.value, 'state':self.state, 'count':count, 'size': size}
        html=render_to_string("textinput.html", context)
        return etree.XML(html)

#-----------------------------------------------------------------------------
# TODO: Make a wrapper for <formulainput>
# TODO: Make an AJAX loop to confirm equation is okay in real-time as user types
class jstextline(GenericInput):
    '''
    Plan: We will inspect element to figure out type
    '''
    js_types = {'formulainput' : 'math'}
    def render(element, value, state, msg=""):
        '''
        textline is used for simple one-line inputs, like formularesponse and symbolicresponse.
        '''
        eid=element.get('id')
        count = int(eid.split('_')[-2])-1 # HACK
        size = element.get('size')
        dojs = element.get('dojs')	# dojs is used for client-side javascript display & return
        				# when dojs=='math', a <span id=display_eid>`{::}`</span>
                                        # and a hidden textarea with id=input_eid_fromjs will be output
        context = {'id':eid, 'value':value, 'state':state, 'count':count, 'size': size,
                   'dojs':dojs,
                   'msg':msg,
                   }
        html=render_to_string("jstext.html", context)
        return etree.XML(html)

#-----------------------------------------------------------------------------
## TODO: Make a wrapper for <codeinput>
class textbox(GenericInput):
    def render(element, value, state, msg=''):
        '''
        The textbox is used for code input.  The message is the return HTML string from
        evaluating the code, eg error messages, and output from the code tests.

        TODO: make this use rows and cols attribs, not size
        '''
        eid=element.get('id')
        count = int(eid.split('_')[-2])-1 # HACK
        size = element.get('size')
        context = {'id':eid, 'value':value, 'state':state, 'count':count, 'size': size, 'msg':msg}
        html=render_to_string("textbox.html", context)
        return etree.XML(html)

#-----------------------------------------------------------------------------
def schematic(element, value, state):
    eid = element.get('id')
    height = element.get('height')
    width = element.get('width')
    parts = element.get('parts')
    analyses = element.get('analyses')
    initial_value = element.get('initial_value')
    submit_analyses = element.get('submit_analyses')
    context = {
        'id':eid,
        'value':value,
        'initial_value':initial_value,
        'state':state,
        'width':width,
        'height':height,
        'parts':parts,
        'analyses':analyses,
        'submit_analyses':submit_analyses,
        }
    html=render_to_string("schematicinput.html", context)
    return etree.XML(html)

#-----------------------------------------------------------------------------
### TODO: Move out of inputtypes
def math(element, value, state, msg=''):
    '''
    This is not really an input type.  It is a convention from Lon-CAPA, used for
    displaying a math equation.

    Examples:

    <m display="jsmath">$\displaystyle U(r)=4 U_0 </m>
    <m>$r_0$</m>     

    We convert these to [mathjax]...[/mathjax] and [mathjaxinline]...[/mathjaxinline]

    TODO: use shorter tags (but this will require converting problem XML files!)
    '''
    mathstr = element.text[1:-1]
    if '\\displaystyle' in mathstr:
        isinline = False
        mathstr = mathstr.replace('\\displaystyle','')
    else:
        isinline = True

    html=render_to_string("mathstring.html",{'mathstr':mathstr,'isinline':isinline,'tail':element.tail})
    xhtml = etree.XML(html)
    # xhtml.tail = element.tail	# don't forget to include the tail!
    return xhtml

#-----------------------------------------------------------------------------

def solution(element, value, state, msg=''):
    '''
    This is not really an input type.  It is just a <span>...</span> which is given an ID,
    that is used for displaying an extended answer (a problem "solution") after "show answers"
    is pressed.  Note that the solution content is NOT sent with the HTML. It is obtained
    by a JSON call.
    '''
    eid=element.get('id')
    size = element.get('size')
    context = {'id':eid,
               'value':value,
               'state':state,
               'size': size,
               'msg':msg,
               }
    html=render_to_string("solutionspan.html", context)
    return etree.XML(html)

#-----------------------------------------------------------------------------

def imageinput(element, value, status, msg=''):
    '''
    Clickable image as an input field.  Element should specify the image source, height, and width, eg
    <imageinput src="/static/Physics801/Figures/Skier-conservation of energy.jpg"  width="388" height="560" />

    TODO: showanswer for imageimput does not work yet - need javascript to put rectangle over acceptable area of image.

    '''
    eid = element.get('id')
    src = element.get('src')
    height = element.get('height')
    width = element.get('width')

    # if value is of the form [x,y] then parse it and send along coordinates of previous answer
    m = re.match('\[([0-9]+),([0-9]+)]',value.strip().replace(' ',''))
    if m:
        (gx,gy) = [int(x)-15 for x in m.groups()]
    else:
        (gx,gy) = (0,0)
    
    context = {
        'id':eid,
        'value':value,
        'height': height,
        'width' : width,
        'src':src,
        'gx':gx,
        'gy':gy,
        'state' : status,	# to change
        'msg': msg,			# to change
        }
    if settings.DEBUG:
        print '[courseware.capa.inputtypes.imageinput] context=',context
    html=render_to_string("imageinput.html", context)
    return etree.XML(html)

