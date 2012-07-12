import json
import logging

from lxml import etree

from x_module import XModule, XModuleDescriptor
from progress import Progress

log = logging.getLogger("mitx.courseware.modules")

class ModuleDescriptor(XModuleDescriptor):
    pass

class Module(XModule):
    id_attribute = 'youtube'
    video_time = 0

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

    def get_state(self):
        log.debug(u"STATE POSITION {0}".format(self.position))
        return json.dumps({ 'position': self.position })

    @classmethod
    def get_xml_tags(c):
        '''Tags in the courseware file guaranteed to correspond to the module'''
        return ["video"]

    def get_html(self):
        return self.system.render_template('video.html', {
            'id': self.item_id,
            'name': self.name,
            'position': self.position,
            'sources': self.sources,
            'annotations': self.annotations,
        })

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)

        xmltree = etree.fromstring(xml)

        self.name = xmltree.get('name')
        self.position = self._init_position(state)
        self.sources = self._init_sources(xmltree)
        self.annotations = self._init_annotations(xmltree)

    def _init_position(self, state):
        position = 0 if state is None else json.loads(state).get('position', 0)
        return position

    def _init_sources(self, xmltree):
        valid_attrs = ['src', 'type' ,'codecs']

        def get_attrib(el):
            return {k:v for k,v in el.attrib.iteritems() if k in valid_attrs}

        sources = []
        elements = [xmltree]
        elements.extend(xmltree.findall('source'))

        for el in elements:
            attrb = get_attrib(el)
            if attrb:
                sources.append(attrb)

        return sources

    def _init_annotations(self, xmltree):
        #  TODO: [rocha] make anotations similar to html5 media
        #  tracks, which can be used for subtitles, alternative
        #  languages, and alternative streams (sign language for
        #  example)
        return []


class VideoSegmentDescriptor(XModuleDescriptor):
    pass
