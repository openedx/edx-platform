# pylint: disable=W0223
"""Video is ungraded Xmodule for support video content.
It's new improved video module, which support additional feature:

- Can play non-YouTube video sources via in-browser HTML5 video player.
- YouTube defaults to HTML5 mode from the start.
- Speed changes in both YouTube and non-YouTube videos happen via
in-browser HTML5 video method (when in HTML5 mode).
- Navigational subtitles can be disabled altogether via an attribute
in XML.
"""

import os
import json
import logging
from operator import itemgetter

from lxml import etree
from pkg_resources import resource_string
import datetime
import copy
from webob import Response
from collections import OrderedDict

from django.conf import settings

from xmodule.x_module import XModule, module_attr
from xmodule.editing_module import TabsEditingDescriptor
from xmodule.raw_module import EmptyDataRawDescriptor
from xmodule.xml_module import is_pointer_tag, name_to_pathname, deserialize_field
from xmodule.exceptions import NotFoundError
from xblock.core import XBlock
from xblock.fields import Scope, String, Float, Boolean, List, Dict, ScopeIds
from xmodule.fields import RelativeTime
from .transcripts_utils import (
    get_or_create_sjson,
    TranscriptException,
    generate_sjson_for_all_speeds,
    youtube_speed_dict,
    Transcript,
)
from .video_utils import create_youtube_string

from xmodule.modulestore.inheritance import InheritanceKeyValueStore
from xblock.runtime import KvsFieldData
from urlparse import urlparse

def get_ext(filename):
    # Prevent incorrectly parsing urls like 'http://abc.com/path/video.mp4?xxxx'.
    path = urlparse(filename).path
    return path.rpartition('.')[-1]


log = logging.getLogger(__name__)


class VideoFields(object):
    """Fields for `VideoModule` and `VideoDescriptor`."""
    display_name = String(
        display_name="Display Name", help="Display name for this module.",
        default="Video",
        scope=Scope.settings
    )
    saved_video_position = RelativeTime(
        help="Current position in the video",
        scope=Scope.user_state,
        default=datetime.timedelta(seconds=0)
    )
    # TODO: This should be moved to Scope.content, but this will
    # require data migration to support the old video module.
    youtube_id_1_0 = String(
        help="This is the Youtube ID reference for the normal speed video.",
        display_name="Youtube ID",
        scope=Scope.settings,
        default="OEoXaMPEzfM"
    )
    youtube_id_0_75 = String(
        help="Optional, for older browsers: the Youtube ID for the .75x speed video.",
        display_name="Youtube ID for .75x speed",
        scope=Scope.settings,
        default=""
    )
    youtube_id_1_25 = String(
        help="Optional, for older browsers: the Youtube ID for the 1.25x speed video.",
        display_name="Youtube ID for 1.25x speed",
        scope=Scope.settings,
        default=""
    )
    youtube_id_1_5 = String(
        help="Optional, for older browsers: the Youtube ID for the 1.5x speed video.",
        display_name="Youtube ID for 1.5x speed",
        scope=Scope.settings,
        default=""
    )
    start_time = RelativeTime(  # datetime.timedelta object
        help="Start time for the video (HH:MM:SS). Max value is 23:59:59.",
        display_name="Start Time",
        scope=Scope.settings,
        default=datetime.timedelta(seconds=0)
    )
    end_time = RelativeTime(  # datetime.timedelta object
        help="End time for the video (HH:MM:SS). Max value is 23:59:59.",
        display_name="End Time",
        scope=Scope.settings,
        default=datetime.timedelta(seconds=0)
    )
    #front-end code of video player checks logical validity of (start_time, end_time) pair.

    # `source` is deprecated field and should not be used in future.
    # `download_video` is used instead.
    source = String(
        help="The external URL to download the video.",
        display_name="Download Video",
        scope=Scope.settings,
        default=""
    )
    download_video = Boolean(
        help="Show a link beneath the video to allow students to download the video. Note: You must add at least one video source below.",
        display_name="Video Download Allowed",
        scope=Scope.settings,
        default=False
    )
    html5_sources = List(
        help="A list of filenames to be used with HTML5 video. The first supported filetype will be displayed.",
        display_name="Video Sources",
        scope=Scope.settings,
    )
    track = String(
        help="The external URL to download the timed transcript track. This appears as a link beneath the video.",
        display_name="Download Transcript",
        scope=Scope.settings,
        default=''
    )
    download_track = Boolean(
        help="Show a link beneath the video to allow students to download the transcript. Note: You must add a link to the HTML5 Transcript field above.",
        display_name="Transcript Download Allowed",
        scope=Scope.settings,
        default=False
    )
    sub = String(
        help="The name of the timed transcript track (for non-Youtube videos).",
        display_name="Transcript (primary)",
        scope=Scope.settings,
        default=""
    )
    show_captions = Boolean(
        help="This controls whether or not captions are shown by default.",
        display_name="Transcript Display",
        scope=Scope.settings,
        default=True
    )
    # Data format: {'de': 'german_translation', 'uk': 'ukrainian_translation'}
    transcripts = Dict(
        help="Add additional transcripts in other languages",
        display_name="Transcript Translations",
        scope=Scope.settings,
        default={}
    )
    transcript_language = String(
        help="Preferred language for transcript",
        display_name="Preferred language for transcript",
        scope=Scope.preferences,
        default="en"
    )
    transcript_download_format = String(
        help="Transcript file format to download by user.",
        scope=Scope.preferences,
        values=[
            {"display_name": "SubRip (.srt) file", "value": "srt"},
            {"display_name": "Text (.txt) file", "value": "txt"}
        ],
        default='srt',
    )
    speed = Float(
        help="The last speed that was explicitly set by user for the video.",
        scope=Scope.user_state,
    )
    global_speed = Float(
        help="Default speed in cases when speed wasn't explicitly for specific video",
        scope=Scope.preferences,
        default=1.0
    )
    youtube_is_available = Boolean(
        help="The availaibility of YouTube API for the user",
        scope=Scope.user_info,
        default=True
    )


class VideoModule(VideoFields, XModule):
    """
    XML source example:

        <video show_captions="true"
            youtube="0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg"
            url_name="lecture_21_3" display_name="S19V3: Vacancies"
        >
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.mp4"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.webm"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.ogv"/>
        </video>
    """
    video_time = 0
    icon_class = 'video'

    # To make sure that js files are called in proper order we use numerical
    # index. We do that to avoid issues that occurs in tests.
    module = __name__.replace('.video_module', '', 2)
    js = {
        'js': [
            resource_string(module, 'js/src/video/00_video_storage.js'),
            resource_string(module, 'js/src/video/00_resizer.js'),
            resource_string(module, 'js/src/video/01_initialize.js'),
            resource_string(module, 'js/src/video/025_focus_grabber.js'),
            resource_string(module, 'js/src/video/02_html5_video.js'),
            resource_string(module, 'js/src/video/03_video_player.js'),
            resource_string(module, 'js/src/video/035_video_accessible_menu.js'),
            resource_string(module, 'js/src/video/04_video_control.js'),
            resource_string(module, 'js/src/video/05_video_quality_control.js'),
            resource_string(module, 'js/src/video/06_video_progress_slider.js'),
            resource_string(module, 'js/src/video/07_video_volume_control.js'),
            resource_string(module, 'js/src/video/08_video_speed_control.js'),
            resource_string(module, 'js/src/video/09_video_caption.js'),
            resource_string(module, 'js/src/video/10_main.js')
        ]
    }
    css = {'scss': [
        resource_string(module, 'css/video/display.scss'),
        resource_string(module, 'css/video/accessible_menu.scss'),
    ]}
    js_module_name = "Video"

    def handle_ajax(self, dispatch, data):
        accepted_keys = [
            'speed', 'saved_video_position', 'transcript_language',
            'transcript_download_format', 'youtube_is_available'
        ]

        conversions = {
            'speed': json.loads,
            'saved_video_position': lambda v: RelativeTime.isotime_to_timedelta(v),
            'youtube_is_available': json.loads,
        }

        if dispatch == 'save_user_state':
            for key in data:
                if hasattr(self, key) and key in accepted_keys:
                    if key in conversions:
                        value = conversions[key](data[key])
                    else:
                        value = data[key]

                    setattr(self, key, value)

                    if key == 'speed':
                        self.global_speed = self.speed

            return json.dumps({'success': True})

        log.debug(u"GET {0}".format(data))
        log.debug(u"DISPATCH {0}".format(dispatch))

        raise NotFoundError('Unexpected dispatch type')

    def get_html(self):
        track_url = None
        transcript_download_format = self.transcript_download_format

        sources = {get_ext(src): src for src in self.html5_sources}

        if self.download_video:
            if self.source:
                sources['main'] = self.source
            elif self.html5_sources:
                sources['main'] = self.html5_sources[0]

        if self.download_track:
            if self.track:
                track_url = self.track
                transcript_download_format = None
            elif self.sub or self.transcripts:
                track_url = self.runtime.handler_url(self, 'transcript').rstrip('/?') + '/download'

        if not self.transcripts:
            transcript_language = u'en'
            languages = {'en': 'English'}
        else:
            if self.transcript_language in self.transcripts:
                transcript_language = self.transcript_language
            elif self.sub:
                transcript_language = u'en'
            else:
                transcript_language = sorted(self.transcripts.keys())[0]

            languages = {
                lang: display
                for lang, display in settings.ALL_LANGUAGES
                if lang in self.transcripts
            }

            if self.sub:
                languages['en'] = 'English'

        # OrderedDict for easy testing of rendered context in tests
        sorted_languages = OrderedDict(sorted(languages.items(), key=itemgetter(1)))

        return self.system.render_template('video.html', {
            'ajax_url': self.system.ajax_url + '/save_user_state',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', False),
            # This won't work when we move to data that
            # isn't on the filesystem
            'data_dir': getattr(self, 'data_dir', None),
            'display_name': self.display_name_with_default,
            'end': self.end_time.total_seconds(),
            'id': self.location.html_id(),
            'show_captions': json.dumps(self.show_captions),
            'sources': sources,
            'speed': json.dumps(self.speed),
            'general_speed': self.global_speed,
            'saved_video_position': self.saved_video_position.total_seconds(),
            'start': self.start_time.total_seconds(),
            'sub': self.sub,
            'track': track_url,
            'youtube_streams': create_youtube_string(self),
            # TODO: Later on the value 1500 should be taken from some global
            # configuration setting field.
            'yt_test_timeout': 1500,
            'yt_test_url': settings.YOUTUBE_TEST_URL,
            'transcript_download_format': transcript_download_format,
            'transcript_download_formats_list': self.descriptor.fields['transcript_download_format'].values,
            'transcript_language': transcript_language,
            'transcript_languages': json.dumps(sorted_languages),
            'transcript_translation_url': self.runtime.handler_url(self, 'transcript').rstrip('/?') + '/translation',
            'transcript_available_translations_url': self.runtime.handler_url(self, 'transcript').rstrip('/?') + '/available_translations',
        })

    def get_transcript(self, transcript_format='srt'):
        """
        Returns transcript, filename and MIME type.

        Raises:
            - NotFoundError if cannot find transcript file in storage.
            - ValueError if transcript file is empty or incorrect JSON.
            - KeyError if transcript file has incorrect format.

        If language is 'en', self.sub should be correct subtitles name.
        If language is 'en', but if self.sub is not defined, this means that we
        should search for video name in order to get proper transcript (old style courses).
        If language is not 'en', give back transcript in proper language and format.
        """
        lang = self.transcript_language

        if lang == 'en':
            if self.sub:  # HTML5 case and (Youtube case for new style videos)
                transcript_name = self.sub
            elif self.youtube_id_1_0:  # old courses
                transcript_name = self.youtube_id_1_0
            else:
                log.debug("No subtitles for 'en' language")
                raise ValueError

            data = Transcript.asset(self.location, transcript_name, lang).data
            filename = '{}.{}'.format(transcript_name, transcript_format)
            content = Transcript.convert(data, 'sjson', transcript_format)
        else:
            data = Transcript.asset(self.location, None, None, self.transcripts[lang]).data
            filename = '{}.{}'.format(os.path.splitext(self.transcripts[lang])[0], transcript_format)
            content = Transcript.convert(data, 'srt', transcript_format)

        if not content:
            log.debug('no subtitles produced in get_transcript')
            raise ValueError

        mime_type = 'text/plain' if transcript_format == 'txt' else 'application/x-subrip'

        return content, filename, mime_type


    @XBlock.handler
    def transcript(self, request, dispatch):
        """
        Entry point for transcript handlers.

        Request GET should contains 2-char language code for `download`
        and additionally `videoId` for `translation`.

        Dispatches:
        `download`: returns SRT file.
        `translation`: returns jsoned translation text.
        `available_translations`: returns list of languages, for which SRT files exist. For 'en' check if SJSON exists.
        """
        if dispatch == 'translation':
            if 'language' not in request.GET:
                log.info("Invalid /transcript GET parameters.")
                return Response(status=400)

            lang = request.GET.get('language')
            if lang not in ['en'] + self.transcripts.keys():
                log.info("Video: transcript facilities are not available for given language.")
                return Response(status=404)
            if lang != self.transcript_language:
                self.transcript_language = lang

            try:
                transcript = self.translation(request.GET.get('videoId', None))
            except (TranscriptException, NotFoundError) as ex:
                log.info(ex.message)
                response = Response(status=404)
            else:
                response = Response(transcript)
                response.content_type = 'application/json'

        elif dispatch == 'download':
            try:
                transcript_content, transcript_filename, transcript_mime_type = self.get_transcript(self.transcript_download_format)
            except (NotFoundError, ValueError, KeyError):
                log.debug("Video@download exception")
                response = Response(status=404)
            else:
                response = Response(
                    transcript_content,
                    headerlist=[
                        ('Content-Disposition', 'attachment; filename="{}"'.format(transcript_filename)),
                    ]
                )
                response.content_type = transcript_mime_type

        elif dispatch == 'available_translations':
            available_translations = []
            if self.sub:  # check if sjson exists for 'en'.
                try:
                    Transcript.asset(self.location, self.sub, 'en')
                except NotFoundError:
                    pass
                else:
                    available_translations = ['en']
            for lang in self.transcripts:
                try:
                   Transcript.asset(self.location, None, None, self.transcripts[lang])
                except NotFoundError:
                    continue
                available_translations.append(lang)
            if available_translations:
                response = Response(json.dumps(available_translations))
                response.content_type = 'application/json'
            else:
                response = Response(status=404)
        else:  # unknown dispatch
            log.debug("Dispatch is not allowed")
            response = Response(status=404)

        return response

    def translation(self, youtube_id):
        """
        This is called to get transcript file for specific language.

        youtube_id: str: must be one of youtube_ids or None if HTML video

        Logic flow:

        If youtube_id doesn't exist, we have a video in HTML5 mode. Otherwise,
        video video in Youtube or Flash modes.

        if youtube:
            If english -> give back youtube_id subtitles:
                Return what we have in contentstore for given youtube_id.
            If non-english:
                a) extract youtube_id from srt file name.
                b) try to find sjson by youtube_id and return if successful.
                c) generate sjson from srt for all youtube speeds.
        if non-youtube:
            If english -> give back `sub` subtitles:
                Return what we have in contentstore for given subs_if that is stored in self.sub.
            If non-english:
                a) try to find previously generated sjson.
                b) otherwise generate sjson from srt and return it.

        Filenames naming:
            en: subs_videoid.srt.sjson
            non_en: uk_subs_videoid.srt.sjson

        Raises:
            NotFoundError if for 'en' subtitles no asset is uploaded.
        """

        if youtube_id:
            # Youtube case:
            if self.transcript_language == 'en':
                return Transcript.asset(self.location, youtube_id).data

            youtube_ids = youtube_speed_dict(self)
            assert youtube_id in youtube_ids

            try:
                sjson_transcript = Transcript.asset(self.location, youtube_id, self.transcript_language).data
            except (NotFoundError):
                log.info("Can't find content in storage for %s transcript: generating.", youtube_id)
                generate_sjson_for_all_speeds(
                    self,
                    self.transcripts[self.transcript_language],
                    {speed: youtube_id for youtube_id, speed in youtube_ids.iteritems()},
                    self.transcript_language
                )
                sjson_transcript = Transcript.asset(self.location, youtube_id, self.transcript_language).data

            return sjson_transcript
        else:
            # HTML5 case
            if self.transcript_language == 'en':
                return Transcript.asset(self.location, self.sub).data
            else:
                return get_or_create_sjson(self)


class VideoDescriptor(VideoFields, TabsEditingDescriptor, EmptyDataRawDescriptor):
    """Descriptor for `VideoModule`."""
    module_class = VideoModule
    transcript = module_attr('transcript')

    tabs = [
        {
            'name': "Basic",
            'template': "video/transcripts.html",
            'current': True
        },
        {
            'name': "Advanced",
            'template': "tabs/metadata-edit-tab.html"
        }
    ]

    def __init__(self, *args, **kwargs):
        """
        Mostly handles backward compatibility issues.

        `source` is deprecated field.
        a) If `source` exists and `source` is not `html5_sources`: show `source`
            field on front-end as not-editable but clearable. Dropdown is a new
            field `download_video` and it has value True.
        b) If `source` is cleared it is not shown anymore.
        c) If `source` exists and `source` in `html5_sources`, do not show `source`
            field. `download_video` field has value True.
        """
        super(VideoDescriptor, self).__init__(*args, **kwargs)
        # For backwards compatibility -- if we've got XML data, parse
        # it out and set the metadata fields
        if self.data:
            field_data = self._parse_video_xml(self.data)
            self._field_data.set_many(self, field_data)
            del self.data

        editable_fields = self.editable_metadata_fields

        self.source_visible = False
        if self.source:
            # If `source` field value exist in the `html5_sources` field values,
            # then delete `source` field value and use value from `html5_sources` field.
            if self.source in self.html5_sources:
                self.source = ''  # Delete source field value.
                self.download_video = True
            else:  # Otherwise, `source` field value will be used.
                self.source_visible = True
                download_video = editable_fields['download_video']
                if not download_video['explicitly_set']:
                    self.download_video = True

        # for backward compatibility.
        # If course was existed and was not re-imported by the moment of adding `download_track` field,
        # we should enable `download_track` if following is true:
        download_track = editable_fields['download_track']
        if not download_track['explicitly_set'] and self.track:
            self.download_track = True

    def save_with_metadata(self, user):
        """
        Save module with updated metadata to database."
        """
        self.save()
        self.runtime.modulestore.update_item(self, user.id if user else None)

    @property
    def editable_metadata_fields(self):
        editable_fields = super(VideoDescriptor, self).editable_metadata_fields

        if hasattr(self, 'source_visible'):
            if self.source_visible:
                editable_fields['source']['non_editable'] = True
            else:
                editable_fields.pop('source')

        return editable_fields

    @classmethod
    def from_xml(cls, xml_data, system, id_generator):
        """
        Creates an instance of this descriptor from the supplied xml_data.
        This may be overridden by subclasses

        xml_data: A string of xml that will be translated into data and children for
            this module
        system: A DescriptorSystem for interacting with external resources
        org and course are optional strings that will be used in the generated modules
            url identifiers
        """
        xml_object = etree.fromstring(xml_data)
        url_name = xml_object.get('url_name', xml_object.get('slug'))
        block_type = 'video'
        definition_id = id_generator.create_definition(block_type, url_name)
        usage_id = id_generator.create_usage(definition_id)
        if is_pointer_tag(xml_object):
            filepath = cls._format_filepath(xml_object.tag, name_to_pathname(url_name))
            xml_data = etree.tostring(cls.load_file(filepath, system.resources_fs, usage_id))
        field_data = cls._parse_video_xml(xml_data)
        kvs = InheritanceKeyValueStore(initial_values=field_data)
        field_data = KvsFieldData(kvs)
        video = system.construct_xblock_from_class(
            cls,
            # We're loading a descriptor, so student_id is meaningless
            # We also don't have separate notions of definition and usage ids yet,
            # so we use the location for both
            ScopeIds(None, block_type, definition_id, usage_id),
            field_data,
        )
        return video

    def definition_to_xml(self, resource_fs):
        """
        Returns an xml string representing this module.
        """
        xml = etree.Element('video')
        youtube_string = create_youtube_string(self)
        # Mild workaround to ensure that tests pass -- if a field
        # is set to its default value, we don't need to write it out.
        if youtube_string and youtube_string != '1.00:OEoXaMPEzfM':
            xml.set('youtube', unicode(youtube_string))
        xml.set('url_name', self.url_name)
        attrs = {
            'display_name': self.display_name,
            'show_captions': json.dumps(self.show_captions),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'sub': self.sub,
            'download_track': json.dumps(self.download_track),
            'download_video': json.dumps(self.download_video),
        }
        for key, value in attrs.items():
            # Mild workaround to ensure that tests pass -- if a field
            # is set to its default value, we don't write it out.
            if value:
                if key in self.fields and self.fields[key].is_set_on(self):
                    xml.set(key, unicode(value))

        for source in self.html5_sources:
            ele = etree.Element('source')
            ele.set('src', source)
            xml.append(ele)

        if self.track:
            ele = etree.Element('track')
            ele.set('src', self.track)
            xml.append(ele)

        # sorting for easy testing of resulting xml
        for transcript_language in sorted(self.transcripts.keys()):
            ele = etree.Element('transcript')
            ele.set('language', transcript_language)
            ele.set('src', self.transcripts[transcript_language])
            xml.append(ele)

        return xml

    def get_context(self):
        """
        Extend context by data for transcript basic tab.
        """
        _context = super(VideoDescriptor, self).get_context()

        metadata_fields = copy.deepcopy(self.editable_metadata_fields)

        display_name = metadata_fields['display_name']
        video_url = metadata_fields['html5_sources']
        youtube_id_1_0 = metadata_fields['youtube_id_1_0']

        def get_youtube_link(video_id):
            if video_id:
                return 'http://youtu.be/{0}'.format(video_id)
            else:
                return ''

        _ = self.runtime.service(self, "i18n").ugettext
        video_url.update({
            'help': _('A YouTube URL or a link to a file hosted anywhere on the web.'),
            'display_name': 'Video URL',
            'field_name': 'video_url',
            'type': 'VideoList',
            'default_value': [get_youtube_link(youtube_id_1_0['default_value'])]
        })

        youtube_id_1_0_value = get_youtube_link(youtube_id_1_0['value'])

        if youtube_id_1_0_value:
            video_url['value'].insert(0, youtube_id_1_0_value)

        metadata = {
            'display_name': display_name,
            'video_url': video_url
        }

        _context.update({'transcripts_basic_tab_metadata': metadata})
        return _context

    @classmethod
    def _parse_youtube(cls, data):
        """
        Parses a string of Youtube IDs such as "1.0:AXdE34_U,1.5:VO3SxfeD"
        into a dictionary. Necessary for backwards compatibility with
        XML-based courses.
        """
        ret = {'0.75': '', '1.00': '', '1.25': '', '1.50': ''}

        videos = data.split(',')
        for video in videos:
            pieces = video.split(':')
            try:
                speed = '%.2f' % float(pieces[0])  # normalize speed

                # Handle the fact that youtube IDs got double-quoted for a period of time.
                # Note: we pass in "VideoFields.youtube_id_1_0" so we deserialize as a String--
                # it doesn't matter what the actual speed is for the purposes of deserializing.
                youtube_id = deserialize_field(cls.youtube_id_1_0, pieces[1])
                ret[speed] = youtube_id
            except (ValueError, IndexError):
                log.warning('Invalid YouTube ID: %s', video)
        return ret

    @classmethod
    def _parse_video_xml(cls, xml_data):
        """
        Parse video fields out of xml_data. The fields are set if they are
        present in the XML.
        """
        xml = etree.fromstring(xml_data)
        field_data = {}

        # Convert between key types for certain attributes --
        # necessary for backwards compatibility.
        conversions = {
            # example: 'start_time': cls._example_convert_start_time
        }

        # Convert between key names for certain attributes --
        # necessary for backwards compatibility.
        compat_keys = {
            'from': 'start_time',
            'to': 'end_time'
        }
        sources = xml.findall('source')
        if sources:
            field_data['html5_sources'] = [ele.get('src') for ele in sources]

        track = xml.find('track')
        if track is not None:
            field_data['track'] = track.get('src')

        transcripts = xml.findall('transcript')
        if transcripts:
            field_data['transcripts'] = {tr.get('language'): tr.get('src') for tr in transcripts}

        for attr, value in xml.items():
            if attr in compat_keys:
                attr = compat_keys[attr]
            if attr in cls.metadata_to_strip + ('url_name', 'name'):
                continue
            if attr == 'youtube':
                speeds = cls._parse_youtube(value)
                for speed, youtube_id in speeds.items():
                    # should have made these youtube_id_1_00 for
                    # cleanliness, but hindsight doesn't need glasses
                    normalized_speed = speed[:-1] if speed.endswith('0') else speed
                    # If the user has specified html5 sources, make sure we don't use the default video
                    if youtube_id != '' or 'html5_sources' in field_data:
                        field_data['youtube_id_{0}'.format(normalized_speed.replace('.', '_'))] = youtube_id
            else:
                #  Convert XML attrs into Python values.
                if attr in conversions:
                    value = conversions[attr](value)
                else:
                # We export values with json.dumps (well, except for Strings, but
                # for about a month we did it for Strings also).
                    value = deserialize_field(cls.fields[attr], value)
                field_data[attr] = value

        # For backwards compatibility: Add `source` if XML doesn't have `download_video`
        # attribute.
        if 'download_video' not in field_data and sources:
            field_data['source'] = field_data['html5_sources'][0]

        # For backwards compatibility: if XML doesn't have `download_track` attribute,
        # it means that it is an old format. So, if `track` has some value,
        # `download_track` needs to have value `True`.
        if 'download_track' not in field_data and track is not None:
            field_data['download_track'] = True

        return field_data
