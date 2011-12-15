# For calculator: 
# http://pyparsing.wikispaces.com/file/view/fourFn.py

from x_module import XModule

from xml.dom.minidom import parse, parseString

import json

## TODO: Abstract out from Django
from django.conf import settings
from djangomako.shortcuts import render_to_response, render_to_string

class VideoModule(XModule):
    ''' Implements a generic learning module. 
        Initialized on access with __init__, first time with state=None, and
        then with state
    '''
    id_attribute = 'youtube'
    video_time = 0

    def handle_ajax(self, dispatch, get):
        if dispatch == 'time':
            self.video_time = int(get['time'])
        print self.video_time

        return json.dumps("True")

    def get_state(self):
        return json.dumps({ 'time':self.video_time })

    def get_xml_tags():
        ''' Tags in the courseware file guaranteed to correspond to the module '''
        return "video1"
        
    def get_id_attribute():
        ''' An attribute in the XML scheme that is guaranteed unique. '''
        return "youtube"

    def get_html(self):
        return render_to_string('video.html',{'id':self.item_id,
                                              'time':self.video_time})

    def get_init_js(self):
        ''' JavaScript code to be run when problem is shown. Be aware
        that this may happen several times on the same page
        (e.g. student switching tabs). Common functions should be put
        in the main course .js files for now. ''' 
        return render_to_string('video_init.js',{'id':self.item_id,
                                                 'video_time':self.video_time})

    def get_destroy_js(self):
        return "videoDestroy();"

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state)
        print state
        if state!=None and "time" not in json.loads(state):
            self.video_time = 0
