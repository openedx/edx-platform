# -*- coding: utf-8 -*-
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
import json
import logging
from operator import itemgetter

from lxml import etree
from pkg_resources import resource_string
import copy

from collections import OrderedDict

from django.conf import settings

from xblock.fields import ScopeIds
from xblock.runtime import KvsFieldData

from xmodule.modulestore.inheritance import InheritanceKeyValueStore
from xmodule.x_module import XModule, module_attr
from xmodule.editing_module import TabsEditingDescriptor
from xmodule.raw_module import EmptyDataRawDescriptor
from xmodule.xml_module import is_pointer_tag, name_to_pathname, deserialize_field


from .video_utils import create_youtube_string, get_course_for_item
from .video_xfields import VideoFields
from .video_handlers import VideoStudentViewHandlers, VideoStudioViewHandlers
from .video_scoring import VideoScoringMixin

from urlparse import urlparse


def get_ext(filename):
    # Prevent incorrectly parsing urls like 'http://abc.com/path/video.mp4?xxxx'.
    path = urlparse(filename).path
    return path.rpartition('.')[-1]


log = logging.getLogger(__name__)
_ = lambda text: text


class VideoModule(VideoFields, VideoScoringMixin, VideoStudentViewHandlers, XModule):
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
            resource_string(module, 'js/src/video/00_async_process.js'),
            resource_string(module, 'js/src/video/00_i18n.js'),
            resource_string(module, 'js/src/video/00_abstract_grader.js'),
            resource_string(module, 'js/src/video/00_sjson.js'),
            resource_string(module, 'js/src/video/00_iterator.js'),
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
            resource_string(module, 'js/src/video/10_grader_collection.js'),
            resource_string(module, 'js/src/video/11_grader.js'),
            resource_string(module, 'js/src/video/12_main.js'),
        ]
    }
    css = {'scss': [
        resource_string(module, 'css/video/display.scss'),
        resource_string(module, 'css/video/accessible_menu.scss'),
    ]}
    js_module_name = "Video"

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
                track_url = self.runtime.handler_url(self, 'transcript', 'download').rstrip('/?')

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

            native_languages = {lang: label for lang, label in settings.LANGUAGES if len(lang) == 2}
            languages = {
                lang: native_languages.get(lang, display)
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
            'handout': self.handout,
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
            'yt_api_url': settings.YOUTUBE['API'],
            'yt_test_url': settings.YOUTUBE['TEST_URL'],
            'transcript_download_format': transcript_download_format,
            'transcript_download_formats_list': self.descriptor.fields['transcript_download_format'].values,
            'transcript_language': transcript_language,
            'transcript_languages': json.dumps(sorted_languages),
            'transcript_translation_url': self.runtime.handler_url(self, 'transcript', 'translation').rstrip('/?'),
            'transcript_available_translations_url': self.runtime.handler_url(self, 'transcript', 'available_translations').rstrip('/?'),
            'grade_url': self.runtime.handler_url(self, 'grade_handler').rstrip('/?'),
            'has_score': json.dumps(self.really_has_score),
            'max_score': json.dumps(self.max_score()),
            'module_score': json.dumps(self.module_score),
            'graders': json.dumps(self.graders()),
        })


class VideoDescriptor(VideoFields, VideoStudioViewHandlers, TabsEditingDescriptor, EmptyDataRawDescriptor):
    """
    Descriptor for `VideoModule`.
    """
    module_class = VideoModule
    transcript = module_attr('transcript')
    grade_handler = module_attr('grade_handler')
    graders = module_attr('graders')

    tabs = [
        {
            'name': _("Basic"),
            'template': "video/transcripts.html",
            'current': True
        },
        {
            'name': _("Advanced"),
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
        # For backwards compatibility -- if we've got XML data, parse it out and set the metadata fields
        if self.data:
            field_data = self._parse_video_xml(self.data)
            self._field_data.set_many(self, field_data)
            del self.data

        editable_fields = super(VideoDescriptor, self).editable_metadata_fields

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

        if self.source_visible:
            editable_fields['source']['non_editable'] = True
        else:
            editable_fields.pop('source')

        languages = [{'label': label, 'code': lang} for lang, label in settings.ALL_LANGUAGES if lang != u'en']
        languages.sort(key=lambda l: l['label'])
        editable_fields['transcripts']['languages'] = languages
        editable_fields['transcripts']['type'] = 'VideoTranslations'
        editable_fields['transcripts']['urlRoot'] = self.runtime.handler_url(self, 'studio_transcript', 'translation').rstrip('/?')
        editable_fields['handout']['type'] = 'FileUploader'

        editable_fields.pop('grade_videos')

        # Inheritance does not work for video player descriptor
        # that's why we obtain grade_videos value from course itself.
        # Should be fixed when used outside of Studio.
        if not get_course_for_item(self).grade_videos:
            for field_name in ['has_score', 'scored_on_end', 'scored_on_percent', 'weight']:
                editable_fields.pop(field_name)

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
            'grade_videos': json.dumps(self.grade_videos),
            'has_score': json.dumps(self.has_score),
            'scored_on_end': json.dumps(self.scored_on_end),
            'weight': self.weight,
            'scored_on_percent': self.scored_on_percent,
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

        if self.handout:
            ele = etree.Element('handout')
            ele.set('src', self.handout)
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
            'help': _('The URL for your video. This can be a YouTube URL or a link to an .mp4, .ogg, or .webm video file hosted elsewhere on the Internet.'),
            'display_name': _('Default Video URL'),
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

        handout = xml.find('handout')
        if handout is not None:
            field_data['handout'] = handout.get('src')

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
