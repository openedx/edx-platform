import json
import os

from mitxmako.shortcuts import render_to_response, render_to_string

from x_module import XModule
from lxml import etree

class Module(XModule):
    def get_state(self):
        return json.dumps({ })

    @classmethod
    def get_xml_tags(c):
        ## TODO: Abstract out from filesystem and Django
        ## HACK: For now, this lets us import without abstracting out
        try: 
            from django.conf import settings
            tags = os.listdir(settings.DATA_DIR+'/custom_tags')
        except: 
            print "Could not open tags directory."
            tags = []
        return tags

    def get_html(self):
        return self.html

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)
        xmltree = etree.fromstring(xml)
        filename = xmltree.tag
        params = dict(xmltree.items())
        self.html = render_to_string(filename, params, namespace = 'custom_tags')
