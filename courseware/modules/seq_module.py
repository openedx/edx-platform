from x_module import XModule
from lxml import etree

import json

## TODO: Abstract out from Django
from django.conf import settings
from djangomako.shortcuts import render_to_response, render_to_string

class SequentialModule(XModule):
    ''' Layout module which lays out content in a temporal sequence
    '''
    id_attribute = 'id'

    def get_state(self):
        return json.dumps({ })

    def get_xml_tags():
        return ["sequential", 'tab']
        
    def get_html(self):
        return self.content

    def get_init_js(self):
        return self.init_js

    def get_destroy_js(self):
        return self.destroy_js

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None, track_function=None, render_function = None, meta = None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state, track_function, render_function)
        xmltree=etree.fromstring(xml)

        def j(m): 
            ''' jsonify contents so it can be embedded in a js array
            We also need to split </script> tags so they don't break
            mid-string'''
            if 'init_js' not in m: m['init_js']=""
            if 'type' not in m: m['init_js']=""
            content=json.dumps(m['content']) 
            content=content.replace('</script>', '<"+"/script>') 

            return {'content':content, 
                    "destroy_js":m['destroy_js'], 
                    'init_js':m['init_js'], 
                    'type':m['type']}

        contents=[(e.get("name"),j(render_function(meta, e))) \
                      for e in xmltree]
     
        js=""

        params={'items':contents,
                'id':"seq"}

        # TODO/BUG: Destroy JavaScript should only be called for the active view
        # This calls it for all the views
        # 
        # To fix this, we'd probably want to have some way of assigning unique
        # IDs to sequences. 
        destroy_js="".join([e[1]['destroy_js'] for e in contents if 'destroy_js' in e[1]])
        
        if xmltree.tag == 'sequential':
            self.init_js=js+render_to_string('seq_module.js',params)
            self.destroy_js=destroy_js
            self.content=render_to_string('seq_module.html',params)
        if xmltree.tag == 'tab':
            params['id'] = 'tab'
            self.init_js=js+render_to_string('tab_module.js',params)
            self.destroy_js=destroy_js
            self.content=render_to_string('tab_module.html',params)
