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


from lxml.etree import Element
from lxml import etree

from mitxmako.shortcuts import render_to_string

#-----------------------------------------------------------------------------
#takes the xml tree as 'element', the student's previous answer as 'value', and the graded status as 'state'

def choicegroup(element, value, state):
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
    
def textline(element, value, state):
    eid=element.get('id')
    count = int(eid.split('_')[-2])-1 # HACK
    size = element.get('size')
    context = {'id':eid, 'value':value, 'state':state, 'count':count, 'size': size}
    html=render_to_string("textinput.html", context)
    return etree.XML(html)

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


