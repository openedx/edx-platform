from x_module import XModule
from lxml import etree

import json

## TODO: Abstract out from Django
from django.conf import settings
from djangomako.shortcuts import render_to_response, render_to_string

class VideoModule(XModule):
    #id_attribute = 'youtube'
    video_time = 0

    def handle_ajax(self, dispatch, get):
        print "GET", get
        print "DISPATCH", dispatch
        if dispatch=='goto_position':
            self.position = int(float(get['position']))
            print "NEW POSITION", self.position
            return json.dumps({'success':True})
        raise Http404()

    def get_state(self):
        print "STATE POSITION", self.position
        return json.dumps({ 'position':self.position })

    def get_xml_tags():
        ''' Tags in the courseware file guaranteed to correspond to the module '''
        return "video"
        
    def video_list(self):
        l=self.youtube.split(',')
        l=[i.split(":") for i in l]
        return json.dumps(dict(l))
    
    def get_html(self):
        return render_to_string('video.html',{'streams':self.video_list(),
                                              'id':self.item_id,
                                              'position':self.position})

    def get_init_js(self):
        ''' JavaScript code to be run when problem is shown. Be aware
        that this may happen several times on the same page
        (e.g. student switching tabs). Common functions should be put
        in the main course .js files for now. ''' 
        print "INIT POSITION", self.position
        return render_to_string('video_init.js',{'streams':self.video_list(),
                                                 'id':self.item_id,
                                                 'position':self.position})

    def get_destroy_js(self):
        return "videoDestroy(\""+self.item_id+"\");"

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None, track_function=None, render_function = None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state, track_function, render_function)
        self.youtube = etree.XML(xml).get('youtube')
        self.position = 0
        if state!=None:
            state = json.loads(state)
            if 'position' in state: self.position = int(float(state['position']))
            print "POOSITION IN STATE"
        print "LOAD POSITION", self.position
