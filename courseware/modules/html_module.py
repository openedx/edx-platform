from x_module import XModule
from lxml import etree

import json

## TODO: Abstract out from Django
from django.conf import settings
from djangomako.shortcuts import render_to_response, render_to_string

class HtmlModule(XModule):
    id_attribute = 'filename'

    def get_state(self):
        return json.dumps({ })

    def get_xml_tags():
        return "html"
        
    def get_html(self):
        if self.filename!=None:
            return render_to_string(self.filename, {'id': self.item_id})
        else: 
            xmltree=etree.fromstring(self.xml)
            textlist=[xmltree.text]+[etree.tostring(i) for i in xmltree]+[xmltree.tail]
            textlist=[i for i in textlist if type(i)==str]
            return "".join(textlist)

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None, track_function=None, render_function = None, meta = None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state, track_function, render_function)
        xmltree=etree.fromstring(xml)
        self.filename = None
        filename_l=xmltree.xpath("/html/@filename")
        if len(filename_l)>0:
            self.filename=str(filename_l[0])
