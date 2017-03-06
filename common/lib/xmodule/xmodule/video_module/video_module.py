# -*- coding: utf-8 -*-
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

from openedx.core.lib.cache_utils import memoize_in_request_cache
from xblock.core import XBlock
from xblock.fields import ScopeIds
from xblock.runtime import KvsFieldData
from opaque_keys.edx.locator import AssetLocator

from xmodule.modulestore.inheritance import InheritanceKeyValueStore, own_metadata
from xmodule.x_module import XModule, module_attr
from xmodule.editing_module import TabsEditingDescriptor
from xmodule.raw_module import EmptyDataRawDescriptor
from xmodule.xml_module import is_pointer_tag, name_to_pathname, deserialize_field
from xmodule.exceptions import NotFoundError
from xmodule.contentstore.content import StaticContent

from .transcripts_utils import VideoTranscriptsMixin, Transcript, get_html5_ids
from .video_utils import create_youtube_string, get_poster, rewrite_video_url, format_xml_exception_message
from .bumper_utils import bumperize
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

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


@XBlock.wants('settings')
class VideoModule(VideoFields, VideoTranscriptsMixin, VideoStudentViewHandlers, XModule, LicenseMixin):
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

    #TODO: For each of the following, ensure that any generated html is properly escaped.
    js = {
        'js': [
            resource_string(module, 'js/src/time.js'),
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
            resource_string(module, 'js/src/video/04_video_full_screen.js'),
            resource_string(module, 'js/src/video/05_video_quality_control.js'),
            resource_string(module, 'js/src/video/06_video_progress_slider.js'),
            resource_string(module, 'js/src/video/07_video_volume_control.js'),
            resource_string(module, 'js/src/video/08_video_speed_control.js'),
            resource_string(module, 'js/src/video/09_video_caption.js'),
            resource_string(module, 'js/src/video/09_play_placeholder.js'),
            resource_string(module, 'js/src/video/09_play_pause_control.js'),
            resource_string(module, 'js/src/video/09_play_skip_control.js'),
            resource_string(module, 'js/src/video/09_skip_control.js'),
            resource_string(module, 'js/src/video/09_bumper.js'),
            resource_string(module, 'js/src/video/09_save_state_plugin.js'),
            resource_string(module, 'js/src/video/09_events_plugin.js'),
            resource_string(module, 'js/src/video/09_events_bumper_plugin.js'),
            resource_string(module, 'js/src/video/09_poster.js'),
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

    def get_transcripts_for_student(self, transcripts):
        """Return transcript information necessary for rendering the XModule student view.
        This is more or less a direct extraction from `get_html`.

        Args:
            transcripts (dict): A dict with all transcripts and a sub.

        Returns:
            Tuple of (track_url, transcript_language, sorted_languages)
            track_url -> subtitle download url
            transcript_language -> default transcript language
            sorted_languages -> dictionary of available transcript languages
        """
        track_url = None
        sub, other_lang = transcripts["sub"], transcripts["transcripts"]
        if self.download_track:
            if self.track:
                track_url = self.track
            elif sub or other_lang:
                track_url = self.runtime.handler_url(self, 'transcript', 'download').rstrip('/?')

        transcript_language = self.get_default_transcript_language(transcripts)

        native_languages = {lang: label for lang, label in settings.LANGUAGES if len(lang) == 2}
        languages = {
            lang: native_languages.get(lang, display)
            for lang, display in settings.ALL_LANGUAGES
            if lang in other_lang
        }
        if not other_lang or (other_lang and sub):
            languages['en'] = 'English'

        # OrderedDict for easy testing of rendered context in tests
        sorted_languages = sorted(languages.items(), key=itemgetter(1))

        sorted_languages = OrderedDict(sorted_languages)
        return track_url, transcript_language, sorted_languages

    def get_html(self):
        track_status = (self.download_track and self.track)
        transcript_download_format = self.transcript_download_format if not track_status else None
        sources = filter(None, self.html5_sources)

        download_video_link = None
        branding_info = None
        youtube_streams = ""

        # Determine if there is an alternative source for this video
        # based on user locale.  This exists to support cases where
        # we leverage a geography specific CDN, like China.
        cdn_url = getattr(settings, 'VIDEO_CDN_URL', {}).get(self.system.user_location)

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
                            # function returns None when the url cannot be re-written
                            rewritten_link = rewrite_video_url(cdn_url, url)
                            if rewritten_link:
                                download_video_link = rewritten_link
                            else:
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
        if getattr(self, 'video_speed_optimizations', True) and cdn_url:
            branding_info = BrandingInfoConfig.get_config().get(self.system.user_location)

            for index, source_url in enumerate(sources):
                new_url = rewrite_video_url(cdn_url, source_url)
                if new_url:
                    sources[index] = new_url

        # If there was no edx_video_id, or if there was no download specified
        # for it, we fall back on whatever we find in the VideoDescriptor
        if not download_video_link and self.download_video:
            if self.source:
                download_video_link = self.source
            elif self.html5_sources:
                download_video_link = self.html5_sources[0]

        track_url, transcript_language, sorted_languages = self.get_transcripts_for_student(self.get_transcripts_info())

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

        self.youtube_streams = youtube_streams or create_youtube_string(self)  # pylint: disable=W0201

        settings_service = self.runtime.service(self, 'settings')

        yt_api_key = None
        if settings_service:
            xblock_settings = settings_service.get_settings_bucket(self)
            if xblock_settings and 'YOUTUBE_API_KEY' in xblock_settings:
                yt_api_key = xblock_settings['YOUTUBE_API_KEY']

        metadata = {
            'saveStateUrl': self.system.ajax_url + '/save_user_state',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', False),
            'streams': self.youtube_streams,
            'sub': self.sub,
            'sources': sources,

            # This won't work when we move to data that
            # isn't on the filesystem
            'captionDataDir': getattr(self, 'data_dir', None),

            'showCaptions': json.dumps(self.show_captions),
            'generalSpeed': self.global_speed,
            'speed': self.speed,
            'savedVideoPosition': self.saved_video_position.total_seconds(),
            'start': self.start_time.total_seconds(),
            'end': self.end_time.total_seconds(),
            'transcriptLanguage': transcript_language,
            'transcriptLanguages': sorted_languages,

            # TODO: Later on the value 1500 should be taken from some global
            # configuration setting field.
            'ytTestTimeout': 1500,

            'ytApiUrl': settings.YOUTUBE['API'],
            'ytMetadataUrl': settings.YOUTUBE['METADATA_URL'],
            'ytKey': yt_api_key,

            'transcriptTranslationUrl': self.runtime.handler_url(
                self, 'transcript', 'translation/__lang__'
            ).rstrip('/?'),
            'transcriptAvailableTranslationsUrl': self.runtime.handler_url(
                self, 'transcript', 'available_translations'
            ).rstrip('/?'),

            ## For now, the option "data-autohide-html5" is hard coded. This option
            ## either enables or disables autohiding of controls and captions on mouse
            ## inactivity. If set to true, controls and captions will autohide for
            ## HTML5 sources (non-YouTube) after a period of mouse inactivity over the
            ## whole video. When the mouse moves (or a key is pressed while any part of
            ## the video player is focused), the captions and controls will be shown
            ## once again.
            ##
            ## There is no option in the "Advanced Editor" to set this option. However,
            ## this option will have an effect if changed to "True". The code on
            ## front-end exists.
            'autohideHtml5': False,

            # This is the server's guess at whether youtube is available for
            # this user, based on what was recorded the last time we saw the
            # user, and defaulting to True.
            'recordedYoutubeIsAvailable': self.youtube_is_available,
        }

        bumperize(self)

        context = {
            'bumper_metadata': json.dumps(self.bumper['metadata']),  # pylint: disable=E1101
            'metadata': json.dumps(OrderedDict(metadata)),
            'poster': json.dumps(get_poster(self)),
            'branding_info': branding_info,
            'cdn_eval': cdn_eval,
            'cdn_exp_group': cdn_exp_group,
            'id': self.location.html_id(),
            'display_name': self.display_name_with_default,
            'handout': self.handout,
            'download_video_link': download_video_link,
            'track': track_url,
            'transcript_download_format': transcript_download_format,
            'transcript_download_formats_list': self.descriptor.fields['transcript_download_format'].values,
            'license': getattr(self, "license", None),
        }
        return self.system.render_template('video.html', context)


@XBlock.wants("request_cache")
@XBlock.wants("settings")
class VideoDescriptor(VideoFields, VideoTranscriptsMixin, VideoStudioViewHandlers,
                      TabsEditingDescriptor, EmptyDataRawDescriptor, LicenseMixin):
    """
    Descriptor for `VideoModule`.
    """
    module_class = VideoModule
    transcript = module_attr('transcript')

    show_in_read_only_mode = True

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

        # Force download_video field to default value if it's not explicitly set for backward compatibility.
        if not self.fields['download_video'].is_set_on(self):
            self.download_video = self.download_video
            self.force_save_fields(['download_video'])

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

        # There is an edge case when old_metadata and own_metadata are same and we are importing transcript from youtube
        # then there is a syncing issue where html5_subs are not syncing with youtube sub, We can make sync better by
        # checking if transcript is present for the video and if any html5_ids transcript is not present then trigger
        # the manage_video_subtitles_save to create the missing transcript with particular html5_id.
        if not metadata_was_changed_by_user and self.sub and hasattr(self, 'html5_sources'):
            html5_ids = get_html5_ids(self.html5_sources)
            for subs_id in html5_ids:
                try:
                    Transcript.asset(self.location, subs_id)
                except NotFoundError:
                    # If a transcript does not not exist with particular html5_id then there is no need to check other
                    # html5_ids because we have to create a new transcript with this missing html5_id by turning on
                    # metadata_was_changed_by_user flag.
                    metadata_was_changed_by_user = True
                    break

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

        settings_service = self.runtime.service(self, 'settings')
        if settings_service:
            xb_settings = settings_service.get_settings_bucket(self)
            if not xb_settings.get("licensing_enabled", False) and "license" in editable_fields:
                del editable_fields["license"]

        if self.source_visible:
            editable_fields['source']['non_editable'] = True
        else:
            editable_fields.pop('source')

        languages = [{'label': label, 'code': lang} for lang, label in settings.ALL_LANGUAGES if lang != u'en']
        languages.sort(key=lambda l: l['label'])
        editable_fields['transcripts']['languages'] = languages
        editable_fields['transcripts']['type'] = 'VideoTranslations'
        editable_fields['transcripts']['urlRoot'] = self.runtime.handler_url(
            self,
            'studio_transcript',
            'translation'
        ).rstrip('/?')
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
        id_generator is used to generate course-specific urls and identifiers
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
        field_data = cls._parse_video_xml(xml_object, id_generator)
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
                    try:
                        xml.set(key, unicode(value))
                    except UnicodeDecodeError:
                        exception_message = format_xml_exception_message(self.location, key, value)
                        log.exception(exception_message)
                        # If exception is UnicodeDecodeError set value using unicode 'utf-8' scheme.
                        log.info("Setting xml value using 'utf-8' scheme.")
                        xml.set(key, unicode(value, 'utf-8'))
                    except ValueError:
                        exception_message = format_xml_exception_message(self.location, key, value)
                        log.exception(exception_message)
                        raise

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

        if self.transcripts is not None:
            # sorting for easy testing of resulting xml
            for transcript_language in sorted(self.transcripts.keys()):
                ele = etree.Element('transcript')
                ele.set('language', transcript_language)
                ele.set('src', self.transcripts[transcript_language])
                xml.append(ele)

        if self.edx_video_id and edxval_api:
            try:
                xml.append(edxval_api.export_to_xml(self.edx_video_id))
            except edxval_api.ValVideoNotFoundError:
                pass

        # handle license specifically
        self.add_license_to_xml(xml)

        return xml

    def create_youtube_url(self, youtube_id):
        """

        Args:
            youtube_id: The ID of the video to create a link for

        Returns:
            A full youtube url to the video whose ID is passed in
        """
        if youtube_id:
            return 'https://www.youtube.com/watch?v={0}'.format(youtube_id)
        else:
            return ''

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
            """
            Returns the fully-qualified YouTube URL for the given video identifier
            """
            # First try a lookup in VAL. If we have a YouTube entry there, it overrides the
            # one passed in.
            if self.edx_video_id and edxval_api:
                val_youtube_id = edxval_api.get_url_for_profile(self.edx_video_id, "youtube")
                if val_youtube_id:
                    video_id = val_youtube_id

            return self.create_youtube_url(video_id)

        _ = self.runtime.service(self, "i18n").ugettext
        video_url.update({
            'help': _('The URL for your video. This can be a YouTube URL or a link to an .mp4, .ogg, or .webm video file hosted elsewhere on the Internet.'),  # pylint: disable=line-too-long
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
    def _parse_video_xml(cls, xml, id_generator=None):
        """
        Parse video fields out of xml_data. The fields are set if they are
        present in the XML.

        Arguments:
            id_generator is used to generate course-specific urls and identifiers
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

        course_id = getattr(id_generator, 'target_course_id', None)
        # Update the handout location with current course_id
        if 'handout' in field_data.keys() and course_id:
            handout_location = StaticContent.get_location_from_path(field_data['handout'])
            if isinstance(handout_location, AssetLocator):
                handout_new_location = StaticContent.compute_location(course_id, handout_location.path)
                field_data['handout'] = StaticContent.serialize_asset_key_with_slash(handout_new_location)

        # For backwards compatibility: Add `source` if XML doesn't have `download_video`
        # attribute.
        if 'download_video' not in field_data and sources:
            field_data['source'] = field_data['html5_sources'][0]

        # For backwards compatibility: if XML doesn't have `download_track` attribute,
        # it means that it is an old format. So, if `track` has some value,
        # `download_track` needs to have value `True`.
        if 'download_track' not in field_data and track is not None:
            field_data['download_track'] = True

        video_asset_elem = xml.find('video_asset')
        if (
                edxval_api and
                video_asset_elem is not None and
                'edx_video_id' in field_data
        ):
            # Allow ValCannotCreateError to escape
            edxval_api.import_from_xml(
                video_asset_elem,
                field_data['edx_video_id'],
                course_id=course_id
            )

        # load license if it exists
        field_data = LicenseMixin.parse_license_from_xml(field_data, xml)

        return field_data

    def index_dictionary(self):
        xblock_body = super(VideoDescriptor, self).index_dictionary()
        video_body = {
            "display_name": self.display_name,
        }

        def _update_transcript_for_index(language=None):
            """ Find video transcript - if not found, don't update index """
            try:
                transcripts = self.get_transcripts_info()
                transcript = self.get_transcript(
                    transcripts, transcript_format='txt', lang=language
                )[0].replace("\n", " ")
                transcript_index_name = "transcript_{}".format(language if language else self.transcript_language)
                video_body.update({transcript_index_name: transcript})
            except NotFoundError:
                pass

        if self.sub:
            _update_transcript_for_index()

        # Check to see if there are transcripts in other languages besides default transcript
        if self.transcripts:
            for language in self.transcripts.keys():
                _update_transcript_for_index(language)

        if "content" in xblock_body:
            xblock_body["content"].update(video_body)
        else:
            xblock_body["content"] = video_body
        xblock_body["content_type"] = "Video"

        return xblock_body

    @property
    def request_cache(self):
        """
        Returns the request_cache from the runtime.
        """
        return self.runtime.service(self, "request_cache")

    @memoize_in_request_cache('request_cache')
    def get_cached_val_data_for_course(self, video_profile_names, course_id):
        """
        Returns the VAL data for the requested video profiles for the given course.
        """
        return edxval_api.get_video_info_for_course_and_profiles(unicode(course_id), video_profile_names)

    def student_view_data(self, context=None):
        """
        Returns a JSON representation of the student_view of this XModule.
        The contract of the JSON content is between the caller and the particular XModule.
        """
        context = context or {}

        # If the "only_on_web" field is set on this video, do not return the rest of the video's data
        # in this json view, since this video is to be accessed only through its web view."
        if self.only_on_web:
            return {"only_on_web": True}

        encoded_videos = {}
        val_video_data = {}

        # Check in VAL data first if edx_video_id exists
        if self.edx_video_id:
            video_profile_names = context.get("profiles", ["mobile_low"])

            # get and cache bulk VAL data for course
            val_course_data = self.get_cached_val_data_for_course(video_profile_names, self.location.course_key)
            val_video_data = val_course_data.get(self.edx_video_id, {})

            # Get the encoded videos if data from VAL is found
            if val_video_data:
                encoded_videos = val_video_data.get('profiles', {})

            # If information for this edx_video_id is not found in the bulk course data, make a
            # separate request for this individual edx_video_id, unless cache misses are disabled.
            # This is useful/required for videos that don't have a course designated, such as the introductory video
            # that is shared across many courses.  However, this results in a separate database request so watch
            # out for any performance hit if many such videos exist in a course.  Set the 'allow_cache_miss' parameter
            # to False to disable this fall back.
            elif context.get("allow_cache_miss", "True").lower() == "true":
                try:
                    val_video_data = edxval_api.get_video_info(self.edx_video_id)
                    # Unfortunately, the VAL API is inconsistent in how it returns the encodings, so remap here.
                    for enc_vid in val_video_data.pop('encoded_videos'):
                        if enc_vid['profile'] in video_profile_names:
                            encoded_videos[enc_vid['profile']] = {key: enc_vid[key] for key in ["url", "file_size"]}
                except edxval_api.ValVideoNotFoundError:
                    pass

        # Fall back to other video URLs in the video module if not found in VAL
        if not encoded_videos:
            video_url = self.html5_sources[0] if self.html5_sources else self.source
            if video_url:
                encoded_videos["fallback"] = {
                    "url": video_url,
                    "file_size": 0,  # File size is unknown for fallback URLs
                }

            # Include youtube link if there is no encoding for mobile- ie only a fallback URL or no encodings at all
            # We are including a fallback URL for older versions of the mobile app that don't handle Youtube urls
            if self.youtube_id_1_0:
                encoded_videos["youtube"] = {
                    "url": self.create_youtube_url(self.youtube_id_1_0),
                    "file_size": 0,  # File size is not relevant for external link
                }

        transcripts_info = self.get_transcripts_info()
        transcripts = {
            lang: self.runtime.handler_url(self, 'transcript', 'download', query="lang=" + lang, thirdparty=True)
            for lang in self.available_translations(transcripts_info, verify_assets=False)
        }

        return {
            "only_on_web": self.only_on_web,
            "duration": val_video_data.get('duration', None),
            "transcripts": transcripts,
            "encoded_videos": encoded_videos,
        }
