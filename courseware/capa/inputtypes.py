from djangomako.shortcuts import render_to_response, render_to_string

from lxml.etree import Element
from lxml import etree

class textline(object):
    @staticmethod
    def render(element, value, state):
        eid=element.get('id')
        context = {'id':eid, 'value':value, 'state':state}
        html=render_to_string("textinput.html", context)
        return etree.XML(html)

class schematic(object):
    @staticmethod
    def render(element, value, state):
        eid = element.get('id')
        height = element.get('height')
        width = element.get('width')
        context = {'id':eid, 'value':value, 'state':state, 'width':width, 'height':height}
        html=render_to_string("schematicinput.html", context)
        return etree.XML(html)


