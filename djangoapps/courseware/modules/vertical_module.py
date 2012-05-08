import json

## TODO: Abstract out from Django
from django.conf import settings
from mitxmako.shortcuts import render_to_response, render_to_string

from x_module import XModule
from lxml import etree

class Module(XModule):
    id_attribute = 'id'

    def get_state(self):
        return json.dumps({ })

    @classmethod
    def get_xml_tags(c):
        return ["vertical"]
        
    def get_html(self):
        return render_to_string('vert_module.html',{'items':self.contents})

    def get_init_js(self):
        return self.init_js_text

    def get_destroy_js(self):
        return self.destroy_js_text


    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)
        xmltree=etree.fromstring(xml)
        self.contents=[(e.get("name"),self.render_function(e)) \
                      for e in xmltree]
        self.init_js_text="".join([e[1]['init_js'] for e in self.contents if 'init_js' in e[1]])
        self.destroy_js_text="".join([e[1]['destroy_js'] for e in self.contents if 'destroy_js' in e[1]])
