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
        return render_to_string(self.item_id, {'id': self.item_id})

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state)
