from lxml.etree import Element
from lxml import etree

from mitxmako.shortcuts import render_to_response, render_to_string

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
        parts = element.get('parts')
        analyses = element.get('analyses')
        initial_value = element.get('initial_value')
        context = {
            'id':eid,
            'value':value,
            'initial_value':initial_value,
            'state':state,
            'width':width,
            'height':height,
            'parts':parts,
            'analyses':analyses,
            }
        html=render_to_string("schematicinput.html", context)
        return etree.XML(html)


