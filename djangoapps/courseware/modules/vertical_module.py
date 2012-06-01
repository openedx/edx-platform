import json

from mitxmako.shortcuts import render_to_response, render_to_string

from x_module import XModule, XModuleDescriptor
from lxml import etree

class ModuleDescriptor(XModuleDescriptor):
    pass

class Module(XModule):
    id_attribute = 'id'

    def get_state(self):
        return json.dumps({ })

    @classmethod
    def get_xml_tags(c):
        return ["vertical", "problemset"]
        
    def get_html(self):
        return render_to_string('vert_module.html',{'items':self.contents})

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)
        xmltree=etree.fromstring(xml)
        self.contents=[(e.get("name"),self.render_function(e)) \
                      for e in xmltree]
