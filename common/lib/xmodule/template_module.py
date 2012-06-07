import json

from x_module import XModule, XModuleDescriptor
from lxml import etree

class ModuleDescriptor(XModuleDescriptor):
    pass

class Module(XModule):
    def get_state(self):
        return json.dumps({ })

    @classmethod
    def get_xml_tags(c):
        return ['customtag']

    def get_html(self):
        return self.html

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)
        xmltree = etree.fromstring(xml)
        filename = xmltree[0].text
        params = dict(xmltree.items())
        self.html = self.system.render_template(filename, params, namespace = 'custom_tags')
