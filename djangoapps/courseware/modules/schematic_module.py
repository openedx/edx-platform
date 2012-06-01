import json

## TODO: Abstract out from Django
from django.conf import settings
from mitxmako.shortcuts import render_to_response, render_to_string

from x_module import XModule, XModuleDescriptor

class ModuleDescriptor(XModuleDescriptor):
    pass

class Module(XModule):
    id_attribute = 'id'

    def get_state(self):
        return json.dumps({ })

    @classmethod
    def get_xml_tags(c):
        return ["schematic"]
        
    def get_html(self):
        return '<input type="hidden" class="schematic" name="{item_id}" height="480" width="640">'.format(item_id=self.item_id)

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)

