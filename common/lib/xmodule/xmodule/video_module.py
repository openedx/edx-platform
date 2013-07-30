# pylint: disable=W0223
"""Video is ungraded Xmodule for support video content."""

import json
import logging

from lxml import etree
from pkg_resources import resource_string, resource_listdir
import datetime
import time

from django.http import Http404

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.editing_module import MetadataOnlyEditingDescriptor
from xblock.core import Integer, Scope, String, Float, Boolean

log = logging.getLogger(__name__)


class VideoFields(object):
    """Fields for `VideoModule` and `VideoDescriptor`."""
    display_name = String(
        display_name="Display Name",
        help="This name appears in the horizontal navigation at the top of the page.",
        scope=Scope.settings,
        # it'd be nice to have a useful default but it screws up other things; so,
        # use display_name_with_default for those
        default="Video"
    )
    data = String(
        help="XML data for the problem",
        default='',
        scope=Scope.content
    )
    position = Integer(help="Current position in the video", scope=Scope.user_state, default=0)
    show_captions = Boolean(help="This controls whether or not captions are shown by default.", display_name="Show Captions", scope=Scope.settings, default=True)
    youtube_id_1_0 = String(help="This is the Youtube ID reference for the normal speed video.", display_name="Default Speed", scope=Scope.settings, default="OEoXaMPEzfM")
    youtube_id_0_75 = String(help="The Youtube ID for the .75x speed video.", display_name="Speed: .75x", scope=Scope.settings, default="")
    youtube_id_1_25 = String(help="The Youtube ID for the 1.25x speed video.", display_name="Speed: 1.25x", scope=Scope.settings, default="")
    youtube_id_1_5 = String(help="The Youtube ID for the 1.5x speed video.", display_name="Speed: 1.5x", scope=Scope.settings, default="")
    start_time = Float(help="Time the video starts", display_name="Start Time", scope=Scope.settings, default=0.0)
    end_time = Float(help="Time the video ends", display_name="End Time", scope=Scope.settings, default=0.0)
    source = String(help="The external URL to download the video. This appears as a link beneath the video.", display_name="Download Video", scope=Scope.settings, default="")
    track = String(help="The external URL to download the subtitle track. This appears as a link beneath the video.", display_name="Download Track", scope=Scope.settings, default="")


class VideoModule(VideoFields, XModule):
    """Video Xmodule."""
    video_time = 0
    icon_class = 'video'

    js = {
        'coffee': [
            resource_string(__name__, 'js/src/time.coffee'),
            resource_string(__name__, 'js/src/video/display.coffee')
        ] +
        [resource_string(__name__, 'js/src/video/display/' + filename)
         for filename
         in sorted(resource_listdir(__name__, 'js/src/video/display'))
         if filename.endswith('.coffee')]
    }
    css = {'scss': [resource_string(__name__, 'css/video/display.scss')]}
    js_module_name = "Video"

    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)

    def handle_ajax(self, dispatch, data):
        """This is not being called right now and we raise 404 error."""
        log.debug(u"GET {0}".format(data))
        log.debug(u"DISPATCH {0}".format(dispatch))
        raise Http404()

    def get_instance_state(self):
        """Return information about state (position)."""
        return json.dumps({'position': self.position})

    def get_html(self):
        return self.system.render_template('video.html', {
            'youtube_id_0_75': self.youtube_id_0_75,
            'youtube_id_1_0': self.youtube_id_1_0,
            'youtube_id_1_25': self.youtube_id_1_25,
            'youtube_id_1_5': self.youtube_id_1_5,
            'id': self.location.html_id(),
            'position': self.position,
            'source': self.source,
            'track': self.track,
            'display_name': self.display_name_with_default,
            'caption_asset_path': "/static/subs/",
            'show_captions': 'true' if self.show_captions else 'false',
            'start': self.start_time,
            'end': self.end_time
        })


class VideoDescriptor(VideoFields,
                      MetadataOnlyEditingDescriptor,
                      RawDescriptor):
    module_class = VideoModule

    def __init__(self, *args, **kwargs):
        super(VideoDescriptor, self).__init__(*args, **kwargs)
        # If we don't have a `youtube_id_1_0`, this is an XML course
        # and we parse out the fields.
        if self.data and 'youtube_id_1_0' not in self._model_data:
            _parse_video_xml(self, self.data)

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(MetadataOnlyEditingDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([VideoModule.start_time,
                                    VideoModule.end_time])
        return non_editable_fields

    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None):
        """
        Creates an instance of this descriptor from the supplied xml_data.
        This may be overridden by subclasses

        xml_data: A string of xml that will be translated into data and children for
            this module
        system: A DescriptorSystem for interacting with external resources
        org and course are optional strings that will be used in the generated modules
            url identifiers
        """
        video = super(VideoDescriptor, cls).from_xml(xml_data, system, org, course)
        _parse_video_xml(video, video.data)
        return video

    def definition_to_xml(self, resource_fs):
        """
        Override the base implementation. We don't actually have anything in the 'data' field
        (it's an empty string), so we just return a simple XML element
        """
        return etree.Element('video')


def _parse_video_xml(video, xml_data):
    """
    Parse video fields out of xml_data. The fields are set if they are
    present in the XML.
    """
    xml = etree.fromstring(xml_data)

    display_name = xml.get('display_name')
    if display_name:
        video.display_name = display_name

    youtube = xml.get('youtube')
    if youtube:
        speeds = _parse_youtube(youtube)
        if speeds['0.75']:
            video.youtube_id_0_75 = speeds['0.75']
        if speeds['1.00']:
            video.youtube_id_1_0 = speeds['1.00']
        if speeds['1.25']:
            video.youtube_id_1_25 = speeds['1.25']
        if speeds['1.50']:
            video.youtube_id_1_5 = speeds['1.50']

    show_captions = xml.get('show_captions')
    if show_captions:
        video.show_captions = json.loads(show_captions)

    source = _get_first_external(xml, 'source')
    if source:
        video.source = source

    track = _get_first_external(xml, 'track')
    if track:
        video.track = track

    start_time = _parse_time(xml.get('from'))
    if start_time:
        video.start_time = start_time

    end_time = _parse_time(xml.get('to'))
    if end_time:
        video.end_time = end_time


def _get_first_external(xmltree, tag):
    """
    Returns the src attribute of the nested `tag` in `xmltree`, if it
    exists.
    """
    for element in xmltree.findall(tag):
        src = element.get('src')
        if src:
            return src
    return None


def _parse_youtube(data):
    """
    Parses a string of Youtube IDs such as "1.0:AXdE34_U,1.5:VO3SxfeD"
    into a dictionary. Necessary for backwards compatibility with
    XML-based courses.
    """
    ret = {'0.75': '', '1.00': '', '1.25': '', '1.50': ''}
    if data == '':
        return ret
    videos = data.split(',')
    for video in videos:
        pieces = video.split(':')
        # HACK
        # To elaborate somewhat: in many LMS tests, the keys for
        # Youtube IDs are inconsistent. Sometimes a particular
        # speed isn't present, and formatting is also inconsistent
        # ('1.0' versus '1.00'). So it's necessary to either do
        # something like this or update all the tests to work
        # properly.
        ret['%.2f' % float(pieces[0])] = pieces[1]
    return ret


def _parse_time(str_time):
    """Converts s in '12:34:45' format to seconds. If s is
    None, returns empty string"""
    if str_time is None or str_time == '':
        return ''
    else:
        obj_time = time.strptime(str_time, '%H:%M:%S')
        return datetime.timedelta(
            hours=obj_time.tm_hour,
            minutes=obj_time.tm_min,
            seconds=obj_time.tm_sec
        ).total_seconds()
