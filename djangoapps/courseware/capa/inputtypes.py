#
# File:   courseware/capa/inputtypes.py
#

'''
Module containing the problem elements which render into input objects

- textline
- textbox     (change this to textarea?)
- schemmatic
- choicegroup (for multiplechoice: checkbox, radio, or select option)
- imageinput  (for clickable image)
- optioninput (for option list)

These are matched by *.html files templates/*.html which are mako templates with the actual html.

Each input type takes the xml tree as 'element', the previous answer as 'value', and the graded status as 'status'

'''

# TODO: rename "state" to "status" for all below
# status is currently the answer for the problem ID for the input element,
# but it will turn into a dict containing both the answer and any associated message for the problem ID for the input element.

import re
import shlex # for splitting quoted strings

from django.conf import settings

from lxml.etree import Element
from lxml import etree

from mitxmako.shortcuts import render_to_string

def get_input_xml_tags():
    ''' Eventually, this will be for all registered input types '''
    return SimpleInput.get_xml_tags()

class SimpleInput():# XModule
    ''' Type for simple inputs -- plain HTML with a form element
    State is a dictionary with optional keys: 
    * Value
    * ID
    * Status (answered, unanswered, unsubmitted)
    * Feedback (dictionary containing keys for hints, errors, or other 
      feedback from previous attempt)
    '''

    xml_tags = {} ## Maps tags to functions
    
    @classmethod
    def get_xml_tags(c):
        return c.xml_tags.keys()

    @classmethod
    def get_uses(c):
        return ['capa_input', 'capa_transform']

    def get_html(self):
        return self.xml_tags[self.tag](self.xml, self.value, self.status, self.msg)

    def __init__(self, system, xml, item_id = None, track_url=None, state=None, use = 'capa_input'):
        self.xml = xml
        self.tag = xml.tag
        if not state:
            state = {}
        ## ID should only come from one place. 
        ## If it comes from multiple, we use state first, XML second, and parameter
        ## third. Since we don't make this guarantee, we can swap this around in 
        ## the future if there's a more logical order. 
        if item_id:
            self.id = item_id
        if xml.get('id'):
            self.id = xml.get('id')
        if 'id' in state:
            self.id = state['id']
        self.system = system

        self.value = ''
        if 'value' in state:
            self.value = state['value']

        self.msg = ''
        if 'feedback' in state and 'message' in state['feedback']:
            self.msg = state['feedback']['message']

        self.status = 'unanswered'
        if 'status' in state:
            self.status = state['status']

## TODO
# class SimpleTransform():
#     ''' Type for simple XML to HTML transforms. Examples:
#     * Math tags, which go from LON-CAPA-style m-tags to MathJAX
#     '''
#     xml_tags = {} ## Maps tags to functions
    
#     @classmethod
#     def get_xml_tags(c):
#         return c.xml_tags.keys()

#     @classmethod
#     def get_uses(c):
#         return ['capa_transform']

#     def get_html(self):
#         return self.xml_tags[self.tag](self.xml, self.value, self.status, self.msg)

#     def __init__(self, system, xml, item_id = None, track_url=None, state=None, use = 'capa_input'):
#         self.xml = xml
#         self.tag = xml.tag
#         if not state:
#             state = {}
#         if item_id:
#             self.id = item_id
#         if xml.get('id'):
#             self.id = xml.get('id')
#         if 'id' in state:
#             self.id = state['id']
#         self.system = system

#         self.value = ''
#         if 'value' in state:
#             self.value = state['value']

#         self.msg = ''
#         if 'feedback' in state and 'message' in state['feedback']:
#             self.msg = state['feedback']['message']

#         self.status = 'unanswered'
#         if 'status' in state:
#             self.status = state['status']


def register_render_function(fn, names=None, cls=SimpleInput):
    if names == None:
        SimpleInput.xml_tags[fn.__name__] = fn
    else:
        raise NotImplementedError
    def wrapped():
        return fn
    return wrapped




#-----------------------------------------------------------------------------

@register_render_function
def optioninput(element, value, status, msg=''):
    '''
    Select option input type.

    Example:

    <optioninput options="('Up','Down')" correct="Up"/><text>The location of the sky</text>
    '''
    eid=element.get('id')
    options = element.get('options')
    if not options:
        raise Exception,"[courseware.capa.inputtypes.optioninput] Missing options specification in " + etree.tostring(element)
    oset = shlex.shlex(options[1:-1])
    oset.quotes = "'"
    oset.whitespace = ","
    oset = [x[1:-1] for x  in list(oset)]

    # osetdict = dict([('option_%s_%s' % (eid,x),oset[x]) for x in range(len(oset)) ])	# make dict with IDs
    osetdict = dict([(oset[x],oset[x]) for x in range(len(oset)) ])	# make dict with key,value same
    if settings.DEBUG:
        print '[courseware.capa.inputtypes.optioninput] osetdict=',osetdict
    
    context={'id':eid,
             'value':value,
             'state':status,
             'msg':msg,
             'options':osetdict,
             }

    html=render_to_string("optioninput.html", context)
    return etree.XML(html)

#-----------------------------------------------------------------------------
@register_render_function
def choicegroup(element, value, status, msg=''):
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
    context={'id':eid, 'value':value, 'state':status, 'type':type, 'choices':choices}
    html=render_to_string("choicegroup.html", context)
    return etree.XML(html)

@register_render_function
def textline(element, value, state, msg=""):
    eid=element.get('id')
    count = int(eid.split('_')[-2])-1 # HACK
    size = element.get('size')
    context = {'id':eid, 'value':value, 'state':state, 'count':count, 'size': size, 'msg': msg}
    html=render_to_string("textinput.html", context)
    return etree.XML(html)

#-----------------------------------------------------------------------------

@register_render_function
def js_textline(element, value, status, msg=''):
        '''
        Plan: We will inspect element to figure out type
        '''
        # TODO: Make a wrapper for <formulainput>
        # TODO: Make an AJAX loop to confirm equation is okay in real-time as user types
		## TODO: Code should follow PEP8 (4 spaces per indentation level)
        '''
        textline is used for simple one-line inputs, like formularesponse and symbolicresponse.
        '''
        eid=element.get('id')
        count = int(eid.split('_')[-2])-1 # HACK
        size = element.get('size')
        dojs = element.get('dojs')	# dojs is used for client-side javascript display & return
        				# when dojs=='math', a <span id=display_eid>`{::}`</span>
                                        # and a hidden textarea with id=input_eid_fromjs will be output
        context = {'id':eid, 'value':value, 'state':status, 'count':count, 'size': size,
                   'dojs':dojs,
                   'msg':msg,
                   }
        html=render_to_string("jstext.html", context)
        return etree.XML(html)

#-----------------------------------------------------------------------------
## TODO: Make a wrapper for <codeinput>
@register_render_function
def textbox(element, value, status, msg=''):
        '''
        The textbox is used for code input.  The message is the return HTML string from
        evaluating the code, eg error messages, and output from the code tests.

        TODO: make this use rows and cols attribs, not size
        '''
        eid=element.get('id')
        count = int(eid.split('_')[-2])-1 # HACK
        size = element.get('size')
        if not value: value = element.text	# if no student input yet, then use the default input given by the problem
        context = {'id':eid, 'value':value, 'state':status, 'count':count, 'size': size, 'msg':msg}
        html=render_to_string("textbox.html", context)
        return etree.XML(html)

#-----------------------------------------------------------------------------
@register_render_function
def schematic(element, value, status, msg=''):
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
        'state':status,
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
@register_render_function
def math(element, value, status, msg=''):
    '''
    This is not really an input type.  It is a convention from Lon-CAPA, used for
    displaying a math equation.

    Examples:

    <m display="jsmath">$\displaystyle U(r)=4 U_0 </m>
    <m>$r_0$</m>     

    We convert these to [mathjax]...[/mathjax] and [mathjaxinline]...[/mathjaxinline]

    TODO: use shorter tags (but this will require converting problem XML files!)
    '''
    mathstr = re.sub('\$(.*)\$','[mathjaxinline]\\1[/mathjaxinline]',element.text)
    mtag = 'mathjax'
    if not '\\displaystyle' in mathstr: mtag += 'inline'
    else: mathstr = mathstr.replace('\\displaystyle','')
    mathstr = mathstr.replace('mathjaxinline]','%s]'%mtag)

    #if '\\displaystyle' in mathstr:
    #    isinline = False
    #    mathstr = mathstr.replace('\\displaystyle','')
    #else:
    #    isinline = True
    # html=render_to_string("mathstring.html",{'mathstr':mathstr,'isinline':isinline,'tail':element.tail})

    html = '<html><html>%s</html><html>%s</html></html>' % (mathstr,element.tail)
    xhtml = etree.XML(html)
    # xhtml.tail = element.tail	# don't forget to include the tail!
    return xhtml

#-----------------------------------------------------------------------------

@register_render_function
def solution(element, value, status, msg=''):
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
               'state':status,
               'size': size,
               'msg':msg,
               }
    html=render_to_string("solutionspan.html", context)
    return etree.XML(html)

#-----------------------------------------------------------------------------

@register_render_function
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
