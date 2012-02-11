import json
import logging

from lxml import etree

## TODO: Abstract out from Django
from django.conf import settings
from mitxmako.shortcuts import render_to_response, render_to_string

from x_module import XModule

log = logging.getLogger("mitx.courseware.modules")

class Module(XModule):
    id_attribute = 'youtube'
    video_time = 0

    def handle_ajax(self, dispatch, get):
        log.debug(u"GET {0}".format(get))
        log.debug(u"DISPATCH {0}".format(dispatch))
        if dispatch == 'goto_position':
            self.position = int(float(get['position']))
            log.debug(u"NEW POSITION {0}".format(self.position))
            return json.dumps({'success':True})
        raise Http404()

    def get_state(self):
        log.debug(u"STATE POSITION {0}".format(self.position))
        return json.dumps({ 'position':self.position })

    @classmethod
    def get_xml_tags(c):
        '''Tags in the courseware file guaranteed to correspond to the module'''
        return ["video"]
        
    def video_list(self):
        l = self.youtube.split(',')
        l = [i.split(":") for i in l]
        return json.dumps(dict(l))
    
    def get_html(self):
        return render_to_string('video.html',{'streams':self.video_list(),
                                              'id':self.item_id,
                                              'position':self.position, 
                                              'name':self.name})

    def get_init_js(self):
        '''JavaScript code to be run when problem is shown. Be aware
        that this may happen several times on the same page
        (e.g. student switching tabs). Common functions should be put
        in the main course .js files for now. ''' 
        log.debug(u"INIT POSITION {0}".format(self.position))
        return render_to_string('video_init.js',{'streams':self.video_list(),
                                                 'id':self.item_id,
                                                 'position':self.position})

    def get_destroy_js(self):
        return "videoDestroy(\"{0}\");".format(self.item_id)

    def __init__(self, xml, item_id, ajax_url=None, track_url=None, state=None, track_function=None, render_function = None):
        XModule.__init__(self, xml, item_id, ajax_url, track_url, state, track_function, render_function)
        self.youtube = etree.XML(xml).get('youtube')
        self.name = etree.XML(xml).get('name')
        self.position = 0
        if state != None:
            state = json.loads(state)
            if 'position' in state:
                self.position = int(float(state['position']))
            #log.debug("POSITION IN STATE")
        #log.debug(u"LOAD POSITION {0}".format(self.position))
