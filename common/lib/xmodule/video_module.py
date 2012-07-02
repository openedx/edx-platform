import json
import logging

from lxml import etree

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor

log = logging.getLogger(__name__)


class VideoModule(XModule):
    video_time = 0
    icon_class = 'video'

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
        xmltree = etree.fromstring(self.definition['data'])
        self.youtube = xmltree.get('youtube')
        self.name = xmltree.get('name')
        self.position = 0

        if instance_state is not None:
            state = json.loads(instance_state)
            if 'position' in state:
                self.position = int(float(state['position']))

    def handle_ajax(self, dispatch, get):
        '''
        Handle ajax calls to this video.
        TODO (vshnayder): This is not being called right now, so the position
        is not being saved.
        '''
        log.debug(u"GET {0}".format(get))
        log.debug(u"DISPATCH {0}".format(dispatch))
        if dispatch == 'goto_position':
            self.position = int(float(get['position']))
            log.info(u"NEW POSITION {0}".format(self.position))
            return json.dumps({'success':True})
        raise Http404()

    def get_progress(self):
        ''' TODO (vshnayder): Get and save duration of youtube video, then return
        fraction watched.
        (Be careful to notice when video link changes and update)

        For now, we have no way of knowing if the video has even been watched, so
        just return None.
        '''
        return None

    def get_instance_state(self):
        log.debug(u"STATE POSITION {0}".format(self.position))
        return json.dumps({'position': self.position})

    def video_list(self):
        return self.youtube

    def get_html(self):
        return self.system.render_template('video.html', {
            'streams': self.video_list(),
            'id': self.location.html_id(),
            'position': self.position,
            'name': self.name,
        })


class VideoDescriptor(RawDescriptor):
    module_class = VideoModule
