import json

from lxml import etree

## TODO: Abstract out from Django
from django.http import Http404
from django.conf import settings
from mitxmako.shortcuts import render_to_response, render_to_string

from x_module import XModule

class SequentialModule(XModule):
    ''' Layout module which lays out content in a temporal sequence
    '''
    id_attribute = 'id'

    def get_state(self):
        return json.dumps({ 'position':self.position })

    def get_xml_tags():
        return ["sequential", 'tab']
        
    def get_html(self):
        self.render()
        return self.content

    def get_init_js(self):
        self.render()
        return self.init_js

    def get_destroy_js(self):
        self.render()
        return self.destroy_js

    def handle_ajax(self, dispatch, get):
        print "GET", get
        print "DISPATCH", dispatch
        if dispatch=='goto_position':
            self.position = int(get['position'])
            return json.dumps({'success':True})
        raise Http404()

    def render(self):
        if self.rendered:
            return
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

        self.contents=[(e.get("name"),j(self.render_function(e))) \
                      for e in self.xmltree]
     
        js=""

        params={'items':self.contents,
                'id':self.item_id,
                'position': self.position}

        # TODO/BUG: Destroy JavaScript should only be called for the active view
        # This calls it for all the views
        # 
        # To fix this, we'd probably want to have some way of assigning unique
        # IDs to sequences. 
        destroy_js="".join([e[1]['destroy_js'] for e in self.contents if 'destroy_js' in e[1]])

        if self.xmltree.tag == 'sequential':
            self.init_js=js+render_to_string('seq_module.js',params)
            self.destroy_js=destroy_js
            self.content=render_to_string('seq_module.html',params)
        if self.xmltree.tag == 'tab':
            params['id'] = 'tab'
            self.init_js=js+render_to_string('tab_module.js',params)
            self.destroy_js=destroy_js
            self.content=render_to_string('tab_module.html',params)
        self.rendered = True
        


    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None, track_function=None, render_function = None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state, track_function, render_function)
        self.xmltree=etree.fromstring(xml)

        self.position = 1

        if state!=None:
            state = json.loads(state)
            if 'position' in state: self.position = int(state['position'])

        self.rendered = False
