import json
import os

## TODO: Abstract out from Django
from django.conf import settings
from mitxmako.shortcuts import render_to_response, render_to_string

from x_module import XModule
from lxml import etree

class Module(XModule):
    def get_state(self):
        return json.dumps({ })

    @classmethod
    def get_xml_tags(c):
        tags = os.listdir(settings.DATA_DIR+'/custom_tags')
        return tags

    def get_html(self):
        return self.html

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None, track_function=None, render_function = None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state, track_function, render_function)
        xmltree = etree.fromstring(xml)
        filename = xmltree.tag
        params = dict(xmltree.items())
#        print params
        self.html = render_to_string('custom_tags/'+filename, params, namespace = 'custom_tags')
