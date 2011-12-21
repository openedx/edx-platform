from x_module import XModule

from xml.dom.minidom import parse, parseString

import json

## TODO: Abstract out from Django
from django.conf import settings
from djangomako.shortcuts import render_to_response, render_to_string

class SchematicModule(XModule):
    id_attribute = 'id'

    def get_state(self):
        return json.dumps({ })

    def get_xml_tags():
        return "schematic"
        
    def get_html(self):
        return '<input type="hidden" class="schematic" name="{item_id}" height="480" width="640">'.format(item_id=self.item_id)

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state)

