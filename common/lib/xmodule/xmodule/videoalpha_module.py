# pylint: disable=W0223
"""VideoAlpha is ungraded Xmodule for support video content.
It's new improved video module, which support additional feature:

- Can play non-YouTube video sources via in-browser HTML5 video player.
- YouTube defaults to HTML5 mode from the start.
- Speed changes in both YouTube and non-YouTube videos happen via
in-browser HTML5 video method (when in HTML5 mode).
- Navigational subtitles can be disabled altogether via an attribute
in XML.
"""

import json
import logging

from lxml import etree
from pkg_resources import resource_string, resource_listdir

from django.http import Http404
from django.conf import settings

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.modulestore.mongo import MongoModuleStore
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.content import StaticContent
from xblock.core import Integer, Scope, String

import datetime
import time
import textwrap

log = logging.getLogger(__name__)


class VideoAlphaFields(object):
    """Fields for `VideoAlphaModule` and `VideoAlphaDescriptor`."""
    data = String(help="XML data for the problem",
                  default=textwrap.dedent('''\
                       <videoalpha show_captions="true" sub="name_of_file" youtube="0.75:JMD_ifUUfsU,1.0:OEoXaMPEzfM,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" >
                           <source src="https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.mp4"/>
                           <source src="https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.webm"/>
                           <source src="https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.ogv"/>
                       </videoalpha>'''),
                  scope=Scope.content)
    position = Integer(help="Current position in the video", scope=Scope.user_state, default=0)
    display_name = String(
        display_name="Display Name", help="Display name for this module",
        default="Video Alpha",
        scope=Scope.settings
    )


class VideoAlphaModule(VideoAlphaFields, XModule):
    """
    XML source example:

        <videoalpha show_captions="true"
            youtube="0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg"
            url_name="lecture_21_3" display_name="S19V3: Vacancies"
        >
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.mp4"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.webm"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.ogv"/>
        </videoalpha>
    """
    video_time = 0
    icon_class = 'video'

    js = {
        'js': [
            resource_string(__name__, 'js/src/videoalpha/display/initialize.js'),
            resource_string(__name__, 'js/src/videoalpha/display/html5_video.js'),
            resource_string(__name__, 'js/src/videoalpha/display/video_player.js'),
            resource_string(__name__, 'js/src/videoalpha/display/video_control.js'),
            resource_string(__name__, 'js/src/videoalpha/display/video_quality_control.js'),
            resource_string(__name__, 'js/src/videoalpha/display/video_progress_slider.js'),
            resource_string(__name__, 'js/src/videoalpha/display/video_volume_control.js'),
            resource_string(__name__, 'js/src/videoalpha/display/video_speed_control.js'),
            resource_string(__name__, 'js/src/videoalpha/display/video_caption.js'),
            resource_string(__name__, 'js/src/videoalpha/main.js')
        ]
    }
    css = {'scss': [resource_string(__name__, 'css/videoalpha/display.scss')]}
    js_module_name = "VideoAlpha"

    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)
        xmltree = etree.fromstring(self.data)

        # Front-end expects an empty string, or a properly formatted string with YouTube IDs.
        self.youtube_streams = xmltree.get('youtube', '')

        self.sub = xmltree.get('sub')

        self.autoplay = xmltree.get('autoplay') or ''
        if self.autoplay.lower() not in ['true', 'false']:
            self.autoplay = 'true'

        self.position = 0
        self.show_captions = xmltree.get('show_captions', 'true')
        self.sources = {
            'main': self._get_source(xmltree),
            'mp4': self._get_source(xmltree, ['mp4']),
            'webm': self._get_source(xmltree, ['webm']),
            'ogv': self._get_source(xmltree, ['ogv']),
        }
        self.track = self._get_track(xmltree)
        self.start_time, self.end_time = self.get_timeframe(xmltree)

    def _get_source(self, xmltree, exts=None):
        """Find the first valid source, which ends with one of `exts`."""
        exts = ['mp4', 'ogv', 'avi', 'webm'] if exts is None else exts
        condition = lambda src: any([src.endswith(ext) for ext in exts])
        return self._get_first_external(xmltree, 'source', condition)

    def _get_track(self, xmltree):
        """Find the first valid track."""
        return self._get_first_external(xmltree, 'track')

    def _get_first_external(self, xmltree, tag, condition=bool):
        """Will return the first 'valid' element of the given tag.
        'valid' means that `condition('src' attribute) == True`
        """
        result = None

        for element in xmltree.findall(tag):
            src = element.get('src')
            if condition(src):
                result = src
                break
        return result

    def get_timeframe(self, xmltree):
        """ Converts 'start_time' and 'end_time' parameters in video tag to seconds.
        If there are no parameters, returns empty string. """

        def parse_time(str_time):
            """Converts s in '12:34:45' format to seconds. If s is
            None, returns empty string"""
            if str_time is None:
                return ''
            else:
                obj_time = time.strptime(str_time, '%H:%M:%S')
                return datetime.timedelta(
                    hours=obj_time.tm_hour,
                    minutes=obj_time.tm_min,
                    seconds=obj_time.tm_sec
                ).total_seconds()

        return parse_time(xmltree.get('start_time')), parse_time(xmltree.get('end_time'))

    def handle_ajax(self, dispatch, data):
        """This is not being called right now and we raise 404 error."""
        log.debug(u"GET {0}".format(data))
        log.debug(u"DISPATCH {0}".format(dispatch))
        raise Http404()

    def get_instance_state(self):
        """Return information about state (position)."""
        return json.dumps({'position': self.position})

    def get_html(self):
        if isinstance(modulestore(), MongoModuleStore):
            caption_asset_path = StaticContent.get_base_url_path_for_course_assets(self.location) + '/subs_'
        else:
            # VS[compat]
            # cdodge: filesystem static content support.
            caption_asset_path = "/static/subs/"

        return self.system.render_template('videoalpha.html', {
            'youtube_streams': self.youtube_streams,
            'id': self.location.html_id(),
            'sub': self.sub,
            'autoplay': self.autoplay,
            'sources': self.sources,
            'track': self.track,
            'display_name': self.display_name_with_default,
            # This won't work when we move to data that
            # isn't on the filesystem
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': caption_asset_path,
            'show_captions': self.show_captions,
            'start': self.start_time,
            'end': self.end_time,
            'autoplay': settings.MITX_FEATURES.get('AUTOPLAY_VIDEOS', True)
        })


class VideoAlphaDescriptor(VideoAlphaFields, RawDescriptor):
    """Descriptor for `VideoAlphaModule`."""
    module_class = VideoAlphaModule
