import json
import logging

from lxml import etree
from pkg_resources import resource_string, resource_listdir

from django.http import Http404

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.editing_module import MetadataOnlyEditingDescriptor
from xblock.core import Integer, Scope, String, Boolean, Float

log = logging.getLogger(__name__)

YOUTUBE_SPEEDS = ['.75', '1.0', '1.25', '1.5']


class VideoFields(object):
    position = Integer(help="Current position in the video", scope=Scope.user_state, default=0)
    show_captions = Boolean(help="Whether or not captions are shown", display_name="Show Captions", scope=Scope.settings, default=True)
    youtube_id_1_0 = String(help="Youtube ID for normal speed video", display_name="Normal Speed", scope=Scope.settings, default="OEoXaMPEzfM")
    youtube_id_0_75 = String(help="Youtube ID for .75x speed video", display_name=".75x", scope=Scope.settings, default="JMD_ifUUfsU")
    youtube_id_1_25 = String(help="Youtube ID for 1.25x speed video", display_name="1.25x", scope=Scope.settings, default="AKqURZnYqpk")
    youtube_id_1_5 = String(help="Youtube ID for 1.5x speed video", display_name="1.5x", scope=Scope.settings, default="DYpADpL7jAY")
    start_time = Float(help="Time the video starts", display_name="Start Time", scope=Scope.settings, default=0.0)
    end_time = Float(help="Time the video ends", display_name="End Time", scope=Scope.settings, default=0.0)
    source = String(help="External source to download video", display_name="External Source", scope=Scope.settings, default="")
    track = String(help="External source to download subtitle strack", display_name="External Track", scope=Scope.settings, default="")


class VideoModule(VideoFields, XModule):
    video_time = 0
    icon_class = 'video'

    js = {'coffee':
        [resource_string(__name__, 'js/src/time.coffee'),
         resource_string(__name__, 'js/src/video/display.coffee')] +
        [resource_string(__name__, 'js/src/video/display/' + filename)
         for filename
         in sorted(resource_listdir(__name__, 'js/src/video/display'))
         if filename.endswith('.coffee')]}
    css = {'scss': [resource_string(__name__, 'css/video/display.scss')]}
    js_module_name = "Video"

    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)

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

    def get_html(self):
        return self.system.render_template('video.html', {
            'youtube_id_0_75': self.youtube_id_0_75,
            'normal_speed_video_id': self.youtube_id_1_0,
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

# TODO: (pfogg) I am highly uncertain about inheriting from
# RawDescriptor for the xml-related methods. This makes LMS unit tests
# pass, but this really shouldn't be a RawDescriptor if users can't
# see raw xml.


# also if it's just return super(...)... then we can just remove these methods, ha
class VideoDescriptor(VideoFields,
                      MetadataOnlyEditingDescriptor,
                      RawDescriptor):
    module_class = VideoModule
    stores_state = True
    template_dir_name = "video"

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
        return super(RawDescriptor, cls).from_xml(xml_data, system, org, course)

    def export_to_xml(self, resource_fs):
        """
        Returns an xml string representign this module, and all modules
        underneath it.  May also write required resources out to resource_fs

        Assumes that modules have single parentage (that no module appears twice
        in the same course), and that it is thus safe to nest modules as xml
        children as appropriate.

        The returned XML should be able to be parsed back into an identical
        XModuleDescriptor using the from_xml method with the same system, org,
        and course

        resource_fs is a pyfilesystem object (from the fs package)
        """
        return super(RawDescriptor, self).export_to_xml(resource_fs)
    #     xml = etree.Element('video')
    #     xml.set('youtube', self.video_list())
    #     xml.set('show_captions', self.show_captions)
    #     xml.set('from', self.start_time)
    #     xml.set('to', self.end_time)

    #     source_tag = etree.SubElement(xml, 'source')
    #     source_tag.set('src', self.source)

    #     track_tag = etree.SubElement(xml, 'track')
    #     track_tag.set('src', self.track)

    #     return etree.tostring(xml, pretty_print=True, encoding='utf-8')

    # def video_list(self):
    #     videos = [self.youtube_id_0_75, self.youtube_id_1_0,
    #               self.youtube_id_1_25, self.youtube_id_1_5]
    #     streams = [':'.join((video, youtube_id))
    #                for video, youtube_id
    #                in zip(YOUTUBE_SPEEDS, videos)]
    #     return ','.join(streams)
