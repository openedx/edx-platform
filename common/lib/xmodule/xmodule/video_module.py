import json
import logging

from lxml import etree
from pkg_resources import resource_string, resource_listdir

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor

log = logging.getLogger(__name__)


class VideoModule(XModule):
    video_time = 0
    icon_class = 'video'

    js = {'coffee':
        [resource_string(__name__, 'js/src/time.coffee'),
         resource_string(__name__, 'js/src/video/display.coffee')] +
        [resource_string(__name__, 'js/src/video/display/' + filename)
         for filename
         in sorted(resource_listdir(__name__, 'js/src/video/display'))]}
    css = {'scss': [resource_string(__name__, 'css/video/display.scss')]}
    js_module_name = "Video"

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
                         instance_state, shared_state, **kwargs)
        xmltree = etree.fromstring(self.definition['data'])
        self.youtube = xmltree.get('youtube')
        self.position = 0
        self.show_captions = xmltree.get('show_captions', 'true')
        self.source = self._get_source(xmltree)
        self.track = self._get_track(xmltree)

        if instance_state is not None:
            state = json.loads(instance_state)
            if 'position' in state:
                self.position = int(float(state['position']))

    def _get_source(self, xmltree):
        # find the first valid source
        return self._get_first_external(xmltree, 'source')
        
    def _get_track(self, xmltree):
        # find the first valid track
        return self._get_first_external(xmltree, 'track')
        
    def _get_first_external(self, xmltree, tag):
        """
        Will return the first valid element
        of the given tag.
        'valid' means has a non-empty 'src' attribute
        """
        result = None
        for element in xmltree.findall(tag):
            src = element.get('src')
            if src:
                result = src
                break
        return result

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
            return json.dumps({'success': True})
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
        #log.debug(u"STATE POSITION {0}".format(self.position))
        return json.dumps({'position': self.position})

    def video_list(self):
        return self.youtube

    def get_html(self):
        return self.system.render_template('video.html', {
            'streams': self.video_list(),
            'id': self.location.html_id(),
            'position': self.position,
            'source': self.source,
            'track' : self.track,
            'display_name': self.display_name,
            # TODO (cpennington): This won't work when we move to data that isn't on the filesystem
            'data_dir': self.metadata['data_dir'],
            'show_captions': self.show_captions
        })


class VideoDescriptor(RawDescriptor):
    module_class = VideoModule
    stores_state = True
    template_dir_name = "video"
