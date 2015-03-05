# -*- coding: utf-8 -*-
# pylint: disable=abstract-method
"""Video is ungraded Xmodule for support video content.
It's new improved video module, which support additional feature:
- Can play non-YouTube video sources via in-browser HTML5 video player.
- YouTube defaults to HTML5 mode from the start.
- Speed changes in both YouTube and non-YouTube videos happen via
in-browser HTML5 video method (when in HTML5 mode).
- Navigational subtitles can be disabled altogether via an attribute
in XML.
Examples of html5 videos for manual testing:
    https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.mp4
    https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.webm
    https://s3.amazonaws.com/edx-course-videos/edx-intro/edX-FA12-cware-1_100.ogv
"""
import copy
import json
import logging
import random
from collections import OrderedDict
from operator import itemgetter

from lxml import etree
from pkg_resources import resource_string

from django.conf import settings

from xblock.fields import ScopeIds
from xblock.runtime import KvsFieldData

from xmodule.modulestore.inheritance import InheritanceKeyValueStore, own_metadata
from xmodule.x_module import XModule, module_attr
from xmodule.editing_module import TabsEditingDescriptor
from xmodule.raw_module import EmptyDataRawDescriptor
from xmodule.xml_module import is_pointer_tag, name_to_pathname, deserialize_field
from xmodule.exceptions import NotFoundError

from .transcripts_utils import VideoTranscriptsMixin
from .video_utils import create_youtube_string, get_video_from_cdn
from .video_xfields import VideoFields
from .video_handlers import VideoStudentViewHandlers, VideoStudioViewHandlers

from xmodule.video_module import manage_video_subtitles_save
from xmodule.mixin import LicenseMixin

# The following import/except block for edxval is temporary measure until
# edxval is a proper XBlock Runtime Service.
#
# Here's the deal: the VideoModule should be able to take advantage of edx-val
# (https://github.com/edx/edx-val) to figure out what URL to give for video
# resources that have an edx_video_id specified. edx-val is a Django app, and
# including it causes tests to fail because we run common/lib tests standalone
# without Django dependencies. The alternatives seem to be:
#
# 1. Move VideoModule out of edx-platform.
# 2. Accept the Django dependency in common/lib.
# 3. Try to import, catch the exception on failure, and check for the existence
#    of edxval_api before invoking it in the code.
# 4. Make edxval an XBlock Runtime Service
#
# (1) is a longer term goal. VideoModule should be made into an XBlock and
# extracted from edx-platform entirely. But that's expensive to do because of
# the various dependencies (like templates). Need to sort this out.
# (2) is explicitly discouraged.
# (3) is what we're doing today. The code is still functional when called within
# the context of the LMS, but does not cause failure on import when running
# standalone tests. Most VideoModule tests tend to be in the LMS anyway,
# probably for historical reasons, so we're not making things notably worse.
# (4) is one of the next items on the backlog for edxval, and should get rid
# of this particular import silliness. It's just that I haven't made one before,
# and I was worried about trying it with my deadline constraints.
try:
    import edxval.api as edxval_api
except ImportError:
    edxval_api = None

try:
    from branding.models import BrandingInfoConfig
except ImportError:
    BrandingInfoConfig = None

log = logging.getLogger(__name__)
_ = lambda text: text


class VideoModule(VideoFields, VideoTranscriptsMixin, VideoStudentViewHandlers, XModule):
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
            resource_string(module, 'js/src/video/00_component.js'),
            resource_string(module, 'js/src/video/00_video_storage.js'),
            resource_string(module, 'js/src/video/00_resizer.js'),
            resource_string(module, 'js/src/video/00_async_process.js'),
            resource_string(module, 'js/src/video/00_i18n.js'),
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
            resource_string(module, 'js/src/video/095_video_context_menu.js'),
            resource_string(module, 'js/src/video/10_commands.js'),
            resource_string(module, 'js/src/video/10_main.js')
        ]
    }
    css = {'scss': [
        resource_string(module, 'css/video/display.scss'),
        resource_string(module, 'css/video/accessible_menu.scss'),
    ]}
    js_module_name = "Video"

    def get_transcripts_for_student(self):
        """Return transcript information necessary for rendering the XModule student view.
        This is more or less a direct extraction from `get_html`.
        Returns:
            Tuple of (track_url, transcript_language, sorted_languages)
            track_url -> subtitle download url
            transcript_language -> default transcript language
            sorted_languages -> dictionary of available transcript languages
        """
        track_url = None
        if self.download_track:
            if self.track:
                track_url = self.track
            elif self.sub or self.transcripts:
                track_url = self.runtime.handler_url(self, 'transcript', 'download').rstrip('/?')

        if not self.transcripts:
            transcript_language = u'en'
            languages = {'en': 'English'}
        else:
            transcript_language = self.get_default_transcript_language()

            native_languages = {lang: label for lang, label in settings.LANGUAGES if len(lang) == 2}
            languages = {
                lang: native_languages.get(lang, display)
                for lang, display in settings.ALL_LANGUAGES
                if lang in self.transcripts
            }

            if self.sub:
                languages['en'] = 'English'

        # OrderedDict for easy testing of rendered context in tests
        sorted_languages = sorted(languages.items(), key=itemgetter(1))
        if 'table' in self.transcripts:
            sorted_languages.insert(0, ('table', 'Table of Contents'))

        sorted_languages = OrderedDict(sorted_languages)
        return track_url, transcript_language, sorted_languages

    def get_html(self):
        transcript_download_format = self.transcript_download_format if not (self.download_track and self.track) else None
        sources = filter(None, self.html5_sources)

        download_video_link = None
        branding_info = None
        youtube_streams = ""

        # If we have an edx_video_id, we prefer its values over what we store
        # internally for download links (source, html5_sources) and the youtube
        # stream.
        if self.edx_video_id and edxval_api:
            try:
                val_profiles = ["youtube", "desktop_webm", "desktop_mp4"]
                val_video_urls = edxval_api.get_urls_for_profiles(self.edx_video_id, val_profiles)

                # VAL will always give us the keys for the profiles we asked for, but
                # if it doesn't have an encoded video entry for that Video + Profile, the
                # value will map to `None`

                # add the non-youtube urls to the list of alternative sources
                # use the last non-None non-youtube url as the link to download the video
                for url in [val_video_urls[p] for p in val_profiles if p != "youtube"]:
                    if url:
                        if url not in sources:
                            sources.append(url)
                        if self.download_video:
                            download_video_link = url

                # set the youtube url
                if val_video_urls["youtube"]:
                    youtube_streams = "1.00:{}".format(val_video_urls["youtube"])

            except edxval_api.ValInternalError:
                # VAL raises this exception if it can't find data for the edx video ID. This can happen if the
                # course data is ported to a machine that does not have the VAL data. So for now, pass on this
                # exception and fallback to whatever we find in the VideoDescriptor.
                log.warning("Could not retrieve information from VAL for edx Video ID: %s.", self.edx_video_id)

        # If the user comes from China use China CDN for html5 videos.
        # 'CN' is China ISO 3166-1 country code.
        # Video caching is disabled for Studio. User_location is always None in Studio.
        # CountryMiddleware disabled for Studio.
        cdn_url = getattr(settings, 'VIDEO_CDN_URL', {}).get(self.system.user_location)
        if getattr(self, 'video_speed_optimizations', True) and cdn_url:
            branding_info = BrandingInfoConfig.get_config().get(self.system.user_location)

            for index, source_url in enumerate(sources):
                new_url = get_video_from_cdn(cdn_url, source_url)
                if new_url:
                    sources[index] = new_url

        # If there was no edx_video_id, or if there was no download specified
        # for it, we fall back on whatever we find in the VideoDescriptor
        if not download_video_link and self.download_video:
            if self.source:
                download_video_link = self.source
            elif self.html5_sources:
                download_video_link = self.html5_sources[0]

        track_url, transcript_language, sorted_languages = self.get_transcripts_for_student()

        # CDN_VIDEO_URLS is only to be used here and will be deleted
        # TODO(ali@edx.org): Delete this after the CDN experiment has completed.
        html_id = self.location.html_id()
        if self.system.user_location == 'CN' and \
                settings.FEATURES.get('ENABLE_VIDEO_BEACON', False) and \
                html_id in getattr(settings, 'CDN_VIDEO_URLS', {}).keys():
            cdn_urls = getattr(settings, 'CDN_VIDEO_URLS', {})[html_id]
            cdn_exp_group, new_source = random.choice(zip(range(len(cdn_urls)), cdn_urls))
            if cdn_exp_group > 0:
                sources[0] = new_source
            cdn_eval = True
        else:
            cdn_eval = False
            cdn_exp_group = None

        return self.system.render_template('video.html', {
            'ajax_url': self.system.ajax_url + '/save_user_state',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', False),
            'branding_info': branding_info,
            'cdn_eval': cdn_eval,
            'cdn_exp_group': cdn_exp_group,
            # This won't work when we move to data that
            # isn't on the filesystem
            'data_dir': getattr(self, 'data_dir', None),
            'display_name': self.display_name_with_default,
            'end': self.end_time.total_seconds(),
            'handout': self.handout,
            'id': self.location.html_id(),
            'show_captions': json.dumps(self.show_captions),
            'download_video_link': download_video_link,
            'sources': json.dumps(sources),
            'speed': json.dumps(self.speed),
            'general_speed': self.global_speed,
            'saved_video_position': self.saved_video_position.total_seconds(),
            'start': self.start_time.total_seconds(),
            'sub': self.sub,
            'track': track_url,
            'youtube_streams': youtube_streams or create_youtube_string(self),
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
            'license': getattr(self, "license", None),
        })


class VideoDescriptor(VideoFields, VideoTranscriptsMixin, VideoStudioViewHandlers,
                      TabsEditingDescriptor, EmptyDataRawDescriptor, LicenseMixin):
    """
    Descriptor for `VideoModule`.
    """
    module_class = VideoModule
    transcript = module_attr('transcript')

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
            field_data = self._parse_video_xml(etree.fromstring(self.data))
            self._field_data.set_many(self, field_data)
            del self.data

        self.source_visible = False
        if self.source:
            # If `source` field value exist in the `html5_sources` field values,
            # then delete `source` field value and use value from `html5_sources` field.
            if self.source in self.html5_sources:
                self.source = ''  # Delete source field value.
                self.download_video = True
            else:  # Otherwise, `source` field value will be used.
                self.source_visible = True
                if not self.fields['download_video'].is_set_on(self):
                    self.download_video = True

        # Set download_video field to default value if its not explicitly set for backward compatibility.
        if not self.fields['download_video'].is_set_on(self):
            self.download_video = self.download_video

        # for backward compatibility.
        # If course was existed and was not re-imported by the moment of adding `download_track` field,
        # we should enable `download_track` if following is true:
        if not self.fields['download_track'].is_set_on(self) and self.track:
            self.download_track = True

    def editor_saved(self, user, old_metadata, old_content):
        """
        Used to update video values during `self`:save method from CMS.
        old_metadata: dict, values of fields of `self` with scope=settings which were explicitly set by user.
        old_content, same as `old_metadata` but for scope=content.
        Due to nature of code flow in item.py::_save_item, before current function is called,
        fields of `self` instance have been already updated, but not yet saved.
        To obtain values, which were changed by user input,
        one should compare own_metadata(self) and old_medatada.
        Video player has two tabs, and due to nature of sync between tabs,
        metadata from Basic tab is always sent when video player is edited and saved first time, for example:
        {'youtube_id_1_0': u'3_yD_cEKoCk', 'display_name': u'Video', 'sub': u'3_yD_cEKoCk', 'html5_sources': []},
        that's why these fields will always present in old_metadata after first save. This should be fixed.
        At consequent save requests html5_sources are always sent too, disregard of their change by user.
        That means that html5_sources are always in list of fields that were changed (`metadata` param in save_item).
        This should be fixed too.
        """
        metadata_was_changed_by_user = old_metadata != own_metadata(self)
        if metadata_was_changed_by_user:
            manage_video_subtitles_save(
                self,
                user,
                old_metadata if old_metadata else None,
                generate_translation=True
            )

    def save_with_metadata(self, user):
        """
        Save module with updated metadata to database."
        """
        self.save()
        self.runtime.modulestore.update_item(self, user.id)

    @property
    def editable_metadata_fields(self):
        editable_fields = super(VideoDescriptor, self).editable_metadata_fields

        if self.source_visible:
            editable_fields['source']['non_editable'] = True
        else:
            editable_fields.pop('source')

        languages = [{'label': label, 'code': lang} for lang, label in settings.ALL_LANGUAGES if lang != u'en']
        languages.sort(key=lambda l: l['label'])
        languages.insert(0, {'label': 'Table of Contents', 'code': 'table'})
        editable_fields['transcripts']['languages'] = languages
        editable_fields['transcripts']['type'] = 'VideoTranslations'
        editable_fields['transcripts']['urlRoot'] = self.runtime.handler_url(self, 'studio_transcript', 'translation').rstrip('/?')
        editable_fields['handout']['type'] = 'FileUploader'

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
            xml_object = cls.load_file(filepath, system.resources_fs, usage_id)
            system.parse_asides(xml_object, definition_id, usage_id, id_generator)
        field_data = cls._parse_video_xml(xml_object)
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
        if youtube_string and youtube_string != '1.00:3_yD_cEKoCk':
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
            # First try a lookup in VAL. If we have a YouTube entry there, it overrides the
            # one passed in.
            if self.edx_video_id and edxval_api:
                val_youtube_id = edxval_api.get_url_for_profile(self.edx_video_id, "youtube")
                if val_youtube_id:
                    video_id = val_youtube_id

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
    def _parse_video_xml(cls, xml):
        """
        Parse video fields out of xml_data. The fields are set if they are
        present in the XML.
        """
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
            elif attr in conversions:
                field_data[attr] = conversions[attr](value)
            elif attr not in cls.fields:
                field_data.setdefault('xml_attributes', {})[attr] = value
            else:
                # We export values with json.dumps (well, except for Strings, but
                # for about a month we did it for Strings also).
                field_data[attr] = deserialize_field(cls.fields[attr], value)

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

    def index_dictionary(self):
        xblock_body = super(VideoDescriptor, self).index_dictionary()
        video_body = {
            "display_name": self.display_name,
        }

        def _update_transcript_for_index(language=None):
            """ Find video transcript - if not found, don't update index """
            try:
                transcript = self.get_transcript(transcript_format='txt', lang=language)[0].replace("\n", " ")
                transcript_index_name = "transcript_{}".format(language if language else self.transcript_language)
                video_body.update({transcript_index_name: transcript})
            except NotFoundError:
                pass

        if self.sub:
            _update_transcript_for_index()

        # check to see if there are transcripts in other languages besides default transcript
        if self.transcripts:
            for language in self.transcripts.keys():
                _update_transcript_for_index(language)

        if "content" in xblock_body:
            xblock_body["content"].update(video_body)
        else:
            xblock_body["content"] = video_body
        xblock_body["content_type"] = "Video"

        return xblock_body
