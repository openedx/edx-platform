from x_module import XModule

from xml.dom.minidom import parse, parseString

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
        print "XX",self.item_id
        return render_to_string(self.item_id, {'id': self.item_id})

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None):
        print "item id" , item_id
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state)

#        template_source=module.getAttribute('filename')
#    	return {'content':render_to_string(template_source, {})}

 #       print state
 #       if state!=None and "time" not in json.loads(state):
 #           self.video_time = 0
