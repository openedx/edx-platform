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
from collections import OrderedDict, defaultdict
from operator import itemgetter

import six
from django.conf import settings
from edx_django_utils.cache import RequestCache
from lxml import etree
from opaque_keys.edx.locator import AssetLocator
from web_fragments.fragment import Fragment
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock
from xblock.fields import ScopeIds
from xblock.runtime import KvsFieldData

from openedx.core.djangoapps.video_config.models import HLSPlaybackEnabledFlag, CourseYoutubeBlockedFlag
from openedx.core.djangoapps.video_pipeline.config.waffle import DEPRECATE_YOUTUBE, waffle_flags
from openedx.core.lib.cache_utils import request_cached
from openedx.core.lib.license import LicenseMixin
from xmodule.contentstore.content import StaticContent
from xmodule.editing_module import EditingMixin, TabsEditingMixin
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.inheritance import InheritanceKeyValueStore, own_metadata
from xmodule.raw_module import EmptyDataRawMixin
from xmodule.validation import StudioValidation, StudioValidationMessage
from xmodule.util.xmodule_django import add_webpack_to_fragment
from xmodule.video_module import manage_video_subtitles_save
from xmodule.x_module import (
    PUBLIC_VIEW, STUDENT_VIEW,
    HTMLSnippet, ResourceTemplates, shim_xmodule_js,
    XModuleMixin, XModuleToXBlockMixin, XModuleDescriptorToXBlockMixin,
)
from xmodule.xml_module import XmlMixin, deserialize_field, is_pointer_tag, name_to_pathname

from .bumper_utils import bumperize
from .transcripts_utils import (
    Transcript,
    VideoTranscriptsMixin,
    clean_video_id,
    get_html5_ids,
    get_transcript,
    subs_filename
)
from .video_handlers import VideoStudentViewHandlers, VideoStudioViewHandlers
from .video_utils import create_youtube_string, format_xml_exception_message, get_poster, rewrite_video_url
from .video_xfields import VideoFields

# The following import/except block for edxval is temporary measure until
# edxval is a proper XBlock Runtime Service.
#
# Here's the deal: the VideoBlock should be able to take advantage of edx-val
# (https://github.com/edx/edx-val) to figure out what URL to give for video
# resources that have an edx_video_id specified. edx-val is a Django app, and
# including it causes tests to fail because we run common/lib tests standalone
# without Django dependencies. The alternatives seem to be:
#
# 1. Move VideoBlock out of edx-platform.
# 2. Accept the Django dependency in common/lib.
# 3. Try to import, catch the exception on failure, and check for the existence
#    of edxval_api before invoking it in the code.
# 4. Make edxval an XBlock Runtime Service
#
# (1) is a longer term goal. VideoBlock should be made into an XBlock and
# extracted from edx-platform entirely. But that's expensive to do because of
# the various dependencies (like templates). Need to sort this out.
# (2) is explicitly discouraged.
# (3) is what we're doing today. The code is still functional when called within
# the context of the LMS, but does not cause failure on import when running
# standalone tests. Most VideoBlock tests tend to be in the LMS anyway,
# probably for historical reasons, so we're not making things notably worse.
# (4) is one of the next items on the backlog for edxval, and should get rid
# of this particular import silliness. It's just that I haven't made one before,
# and I was worried about trying it with my deadline constraints.
try:
    import edxval.api as edxval_api
except ImportError:
    edxval_api = None

try:
    from lms.djangoapps.branding.models import BrandingInfoConfig
except ImportError:
    BrandingInfoConfig = None

log = logging.getLogger(__name__)

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text

EXPORT_IMPORT_COURSE_DIR = u'course'
EXPORT_IMPORT_STATIC_DIR = u'static'


@XBlock.wants('settings', 'completion', 'i18n', 'request_cache')
class VideoBlock(
        VideoFields, VideoTranscriptsMixin, VideoStudioViewHandlers, VideoStudentViewHandlers,
        TabsEditingMixin, EmptyDataRawMixin, XmlMixin, EditingMixin,
        XModuleDescriptorToXBlockMixin, XModuleToXBlockMixin, HTMLSnippet, ResourceTemplates, XModuleMixin,
        LicenseMixin):
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
    has_custom_completion = True
    completion_mode = XBlockCompletionMode.COMPLETABLE

    video_time = 0
    icon_class = 'video'

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

    uses_xmodule_styles_setup = True
    requires_per_student_anonymous_id = True

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
        sorted_languages = sorted(list(languages.items()), key=itemgetter(1))

        sorted_languages = OrderedDict(sorted_languages)
        return track_url, transcript_language, sorted_languages

    @property
    def youtube_deprecated(self):
        """
        Return True if youtube is deprecated and hls as primary playback is enabled else False
        """
        # Return False if `hls` playback feature is disabled.
        if not HLSPlaybackEnabledFlag.feature_enabled(self.location.course_key):
            return False

        # check if youtube has been deprecated and hls as primary playback
        # is enabled for this course
        return waffle_flags()[DEPRECATE_YOUTUBE].is_enabled(self.location.course_key)

    def youtube_disabled_for_course(self):
        if not self.location.context_key.is_course:
            return False  # Only courses have this flag
        request_cache = RequestCache('youtube_disabled_for_course')
        cache_response = request_cache.get_cached_response(self.location.context_key)
        if cache_response.is_found:
            return cache_response.value

        youtube_is_disabled = CourseYoutubeBlockedFlag.feature_enabled(self.location.course_key)
        request_cache.set(self.location.context_key, youtube_is_disabled)
        return youtube_is_disabled

    def prioritize_hls(self, youtube_streams, html5_sources):
        """
        Decide whether hls can be prioritized as primary playback or not.

        If both the youtube and hls sources are present then make decision on flag
        If only either youtube or hls is present then play whichever is present
        """
        yt_present = bool(youtube_streams.strip()) if youtube_streams else False
        hls_present = any(source for source in html5_sources if source.strip().endswith('.m3u8'))

        if yt_present and hls_present:
            return self.youtube_deprecated

        return False

    def student_view(self, _context):
        """
        Return the student view.
        """
        fragment = Fragment(self.get_html())
        add_webpack_to_fragment(fragment, 'VideoBlockPreview')
        shim_xmodule_js(fragment, 'Video')
        return fragment

    def author_view(self, context):
        """
        Renders the Studio preview view.
        """
        return self.student_view(context)

    def studio_view(self, _context):
        """
        Return the studio view.
        """
        fragment = Fragment(
            self.system.render_template(self.mako_template, self.get_context())
        )
        add_webpack_to_fragment(fragment, 'VideoBlockStudio')
        shim_xmodule_js(fragment, 'TabsEditingDescriptor')
        return fragment

    def public_view(self, context):
        """
        Returns a fragment that contains the html for the public view
        """
        if getattr(self.runtime, 'suppports_state_for_anonymous_users', False):
            # The new runtime can support anonymous users as fully as regular users:
            return self.student_view(context)

        fragment = Fragment(self.get_html(view=PUBLIC_VIEW))
        add_webpack_to_fragment(fragment, 'VideoBlockPreview')
        shim_xmodule_js(fragment, 'Video')
        return fragment

    def get_html(self, view=STUDENT_VIEW):

        track_status = (self.download_track and self.track)
        transcript_download_format = self.transcript_download_format if not track_status else None
        sources = [source for source in self.html5_sources if source]

        download_video_link = None
        branding_info = None
        youtube_streams = ""
        video_duration = None
        video_status = None

        # Determine if there is an alternative source for this video
        # based on user locale.  This exists to support cases where
        # we leverage a geography specific CDN, like China.
        default_cdn_url = getattr(settings, 'VIDEO_CDN_URL', {}).get('default')
        cdn_url = getattr(settings, 'VIDEO_CDN_URL', {}).get(self.system.user_location, default_cdn_url)

        # If we have an edx_video_id, we prefer its values over what we store
        # internally for download links (source, html5_sources) and the youtube
        # stream.
        if self.edx_video_id and edxval_api:
            try:
                val_profiles = ["youtube", "desktop_webm", "desktop_mp4"]

                if HLSPlaybackEnabledFlag.feature_enabled(self.course_id):
                    val_profiles.append('hls')

                # strip edx_video_id to prevent ValVideoNotFoundError error if unwanted spaces are there. TNL-5769
                val_video_urls = edxval_api.get_urls_for_profiles(self.edx_video_id.strip(), val_profiles)

                # VAL will always give us the keys for the profiles we asked for, but
                # if it doesn't have an encoded video entry for that Video + Profile, the
                # value will map to `None`

                # add the non-youtube urls to the list of alternative sources
                # use the last non-None non-youtube non-hls url as the link to download the video
                for url in [val_video_urls[p] for p in val_profiles if p != "youtube"]:
                    if url:
                        if url not in sources:
                            sources.append(url)
                        # don't include hls urls for download
                        if self.download_video and not url.endswith('.m3u8'):
                            # function returns None when the url cannot be re-written
                            rewritten_link = rewrite_video_url(cdn_url, url)
                            if rewritten_link:
                                download_video_link = rewritten_link
                            else:
                                download_video_link = url

                # set the youtube url
                if val_video_urls["youtube"]:
                    youtube_streams = "1.00:{}".format(val_video_urls["youtube"])

                # get video duration
                video_data = edxval_api.get_video_info(self.edx_video_id.strip())
                video_duration = video_data.get('duration')
                video_status = video_data.get('status')

            except (edxval_api.ValInternalError, edxval_api.ValVideoNotFoundError):
                # VAL raises this exception if it can't find data for the edx video ID. This can happen if the
                # course data is ported to a machine that does not have the VAL data. So for now, pass on this
                # exception and fallback to whatever we find in the VideoBlock.
                log.warning("Could not retrieve information from VAL for edx Video ID: %s.", self.edx_video_id)

        # If the user comes from China use China CDN for html5 videos.
        # 'CN' is China ISO 3166-1 country code.
        # Video caching is disabled for Studio. User_location is always None in Studio.
        # CountryMiddleware disabled for Studio.
        if getattr(self, 'video_speed_optimizations', True) and cdn_url:
            branding_info = BrandingInfoConfig.get_config().get(self.system.user_location)

            if self.edx_video_id and edxval_api and video_status != u'external':
                for index, source_url in enumerate(sources):
                    new_url = rewrite_video_url(cdn_url, source_url)
                    if new_url:
                        sources[index] = new_url

        # If there was no edx_video_id, or if there was no download specified
        # for it, we fall back on whatever we find in the VideoBlock.
        if not download_video_link and self.download_video:
            if self.html5_sources:
                download_video_link = self.html5_sources[0]

            # don't give the option to download HLS video urls
            if download_video_link and download_video_link.endswith('.m3u8'):
                download_video_link = None

        transcripts = self.get_transcripts_info()
        track_url, transcript_language, sorted_languages = self.get_transcripts_for_student(transcripts=transcripts)

        cdn_eval = False
        cdn_exp_group = None

        if self.youtube_disabled_for_course():
            self.youtube_streams = ''
        else:
            self.youtube_streams = youtube_streams or create_youtube_string(self)  # pylint: disable=W0201

        settings_service = self.runtime.service(self, 'settings')
        poster = None
        #### EOL ####
        try:
            if self.edx_video_id:
                from eol_vimeo.models import EolVimeoVideo
                video_vimeo = EolVimeoVideo.objects.get(edx_video_id=self.edx_video_id.strip(), course_key=self.course_id)
                poster = video_vimeo.url_picture
        except Exception as e:
            log.info('EolVimeo - Video id does not exist, edx_video_id: {} or Import Error, error: {}'.format(self.edx_video_id.strip(), str(e)))
        try:
            if sources and sources[0][0] == '/':
                sources[0] = 'https://player.vimeo.com/progressive_redirect/playback{}'.format(sources[0])
            if sources and 'progressive_redirect' in sources[0]:
                import urllib.request
                sources[0] = urllib.request.urlopen(sources[0]).geturl()
        except Exception as e:
            log.info('EolVimeo - Error to get final video url, edx_video_id: {}, error: {}'.format(self.edx_video_id.strip(), str(e)))
        #### EOL END ####
        if not poster and edxval_api and self.edx_video_id:
            poster = edxval_api.get_course_video_image_url(
                course_id=self.runtime.course_id.for_branch(None),
                edx_video_id=self.edx_video_id.strip()
            )

        completion_service = self.runtime.service(self, 'completion')
        if completion_service:
            completion_enabled = completion_service.completion_tracking_enabled()
        else:
            completion_enabled = False

        # This is the setting that controls whether the autoadvance button will be visible, not whether the
        # video will autoadvance or not.
        # For autoadvance controls to be shown, both the feature flag and the course setting must be true.
        # This allows to enable the feature for certain courses only.
        autoadvance_enabled = settings.FEATURES.get('ENABLE_AUTOADVANCE_VIDEOS', False) and \
            getattr(self, 'video_auto_advance', False)

        # This is the current status of auto-advance (not the control visibility).
        # But when controls aren't visible we force it to off. The student might have once set the preference to
        # true, but now staff or admin have hidden the autoadvance button and the student won't be able to disable
        # it anymore; therefore we force-disable it in this case (when controls aren't visible).
        autoadvance_this_video = self.auto_advance and autoadvance_enabled

        metadata = {
            'autoAdvance': autoadvance_this_video,
            # For now, the option "data-autohide-html5" is hard coded. This option
            # either enables or disables autohiding of controls and captions on mouse
            # inactivity. If set to true, controls and captions will autohide for
            # HTML5 sources (non-YouTube) after a period of mouse inactivity over the
            # whole video. When the mouse moves (or a key is pressed while any part of
            # the video player is focused), the captions and controls will be shown
            # once again.
            #
            # There is no option in the "Advanced Editor" to set this option. However,
            # this option will have an effect if changed to "True". The code on
            # front-end exists.
            'autohideHtml5': False,
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', False),
            # This won't work when we move to data that
            # isn't on the filesystem
            'captionDataDir': getattr(self, 'data_dir', None),
            'completionEnabled': completion_enabled,
            'completionPercentage': settings.COMPLETION_VIDEO_COMPLETE_PERCENTAGE,
            'duration': video_duration,
            'end': self.end_time.total_seconds(),  # pylint: disable=no-member
            'generalSpeed': self.global_speed,
            'lmsRootURL': settings.LMS_ROOT_URL,
            'poster': poster,
            'prioritizeHls': self.prioritize_hls(self.youtube_streams, sources),
            'publishCompletionUrl': self.runtime.handler_url(self, 'publish_completion', '').rstrip('?'),
            # This is the server's guess at whether youtube is available for
            # this user, based on what was recorded the last time we saw the
            # user, and defaulting to True.
            'recordedYoutubeIsAvailable': self.youtube_is_available,
            'savedVideoPosition': self.saved_video_position.total_seconds(),  # pylint: disable=no-member
            'saveStateEnabled': view != PUBLIC_VIEW,
            'saveStateUrl': self.ajax_url + '/save_user_state',
            'showCaptions': json.dumps(self.show_captions),
            'sources': sources,
            'speed': self.speed,
            'start': self.start_time.total_seconds(),  # pylint: disable=no-member
            'streams': self.youtube_streams,
            'transcriptAvailableTranslationsUrl': self.runtime.handler_url(
                self, 'transcript', 'available_translations'
            ).rstrip('/?'),
            'transcriptLanguage': transcript_language,
            'transcriptLanguages': sorted_languages,
            'transcriptTranslationUrl': self.runtime.handler_url(
                self, 'transcript', 'translation/__lang__'
            ).rstrip('/?'),
            'ytApiUrl': settings.YOUTUBE['API'],
            'ytMetadataEndpoint': (
                # In the new runtime, get YouTube metadata via a handler. The handler supports anonymous users and
                # can work in sandboxed iframes. In the old runtime, the JS will call the LMS's yt_video_metadata
                # API endpoint directly (not an XBlock handler).
                self.runtime.handler_url(self, 'yt_video_metadata')
                if getattr(self.runtime, 'suppports_state_for_anonymous_users', False) else ''
            ),
            'ytTestTimeout': settings.YOUTUBE['TEST_TIMEOUT'],
        }

        bumperize(self)

        context = {
            'autoadvance_enabled': autoadvance_enabled,
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
            'transcript_download_formats_list': self.fields['transcript_download_format'].values,
            'license': getattr(self, "license", None),
        }
        return self.system.render_template('video.html', context)

    def validate(self):
        """
        Validates the state of this Video XBlock instance. This
        is the override of the general XBlock method, and it will also ask
        its superclass to validate.
        """
        validation = super(VideoBlock, self).validate()
        if not isinstance(validation, StudioValidation):
            validation = StudioValidation.copy(validation)

        no_transcript_lang = []
        for lang_code, transcript in self.transcripts.items():
            if not transcript:
                no_transcript_lang.append([label for code, label in settings.ALL_LANGUAGES if code == lang_code][0])

        if no_transcript_lang:
            ungettext = self.runtime.service(self, "i18n").ungettext
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.WARNING,
                    ungettext(
                        'There is no transcript file associated with the {lang} language.',
                        'There are no transcript files associated with the {lang} languages.',
                        len(no_transcript_lang)
                    ).format(lang=', '.join(sorted(no_transcript_lang)))
                )
            )
        return validation

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
            self.edx_video_id = self.edx_video_id and self.edx_video_id.strip()

            # We want to override `youtube_id_1_0` with val youtube profile in the first place when someone adds/edits
            # an `edx_video_id` or its underlying YT val profile. Without this, override will only happen when a user
            # saves the video second time. This is because of the syncing of basic and advanced video settings which
            # also syncs val youtube id from basic tab's `Video Url` to advanced tab's `Youtube ID`.
            if self.edx_video_id and edxval_api:
                val_youtube_id = edxval_api.get_url_for_profile(self.edx_video_id, 'youtube')
                if val_youtube_id and self.youtube_id_1_0 != val_youtube_id:
                    self.youtube_id_1_0 = val_youtube_id

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
        editable_fields = super(VideoBlock, self).editable_metadata_fields

        settings_service = self.runtime.service(self, 'settings')
        if settings_service:
            xb_settings = settings_service.get_settings_bucket(self)
            if not xb_settings.get("licensing_enabled", False) and "license" in editable_fields:
                del editable_fields["license"]

        # Default Timed Transcript a.k.a `sub` has been deprecated and end users shall
        # not be able to modify it.
        editable_fields.pop('sub')

        languages = [{'label': label, 'code': lang} for lang, label in settings.ALL_LANGUAGES]
        languages.sort(key=lambda l: l['label'])
        editable_fields['transcripts']['custom'] = True
        editable_fields['transcripts']['languages'] = languages
        editable_fields['transcripts']['type'] = 'VideoTranslations'

        # We need to send ajax requests to show transcript status
        # whenever edx_video_id changes on frontend. Thats why we
        # are changing type to `VideoID` so that a specific
        # Backbonjs view can handle it.
        editable_fields['edx_video_id']['type'] = 'VideoID'

        # construct transcripts info and also find if `en` subs exist
        transcripts_info = self.get_transcripts_info()
        possible_sub_ids = [self.sub, self.youtube_id_1_0] + get_html5_ids(self.html5_sources)
        for sub_id in possible_sub_ids:
            try:
                _, sub_id, _ = get_transcript(self, lang=u'en', output_format=Transcript.TXT)
                transcripts_info['transcripts'] = dict(transcripts_info['transcripts'], en=sub_id)
                break
            except NotFoundError:
                continue

        editable_fields['transcripts']['value'] = transcripts_info['transcripts']
        editable_fields['transcripts']['urlRoot'] = self.runtime.handler_url(
            self,
            'studio_transcript',
            'translation'
        ).rstrip('/?')
        editable_fields['handout']['type'] = 'FileUploader'

        return editable_fields

    @classmethod
    def parse_xml_new_runtime(cls, node, runtime, keys):
        """
        Implement the video block's special XML parsing requirements for the
        new runtime only. For all other runtimes, use the existing XModule-style
        methods like .from_xml().
        """
        video_block = runtime.construct_xblock_from_class(cls, keys)
        field_data = cls.parse_video_xml(node)
        for key, val in field_data.items():
            if key not in cls.fields:
                continue  # parse_video_xml returns some old non-fields like 'source'
            setattr(video_block, key, cls.fields[key].from_json(val))
        # Don't use VAL in the new runtime:
        video_block.edx_video_id = None
        return video_block

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
        field_data = cls.parse_video_xml(xml_object, id_generator)
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

        # Update VAL with info extracted from `xml_object`
        video.edx_video_id = video.import_video_info_into_val(
            xml_object,
            system.resources_fs,
            getattr(id_generator, 'target_course_id', None)
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
            xml.set('youtube', six.text_type(youtube_string))
        xml.set('url_name', self.url_name)
        attrs = [
            ('display_name', self.display_name),
            ('show_captions', json.dumps(self.show_captions)),
            ('start_time', self.start_time),
            ('end_time', self.end_time),
            ('sub', self.sub),
            ('download_track', json.dumps(self.download_track)),
            ('download_video', json.dumps(self.download_video))
        ]
        for key, value in attrs:
            # Mild workaround to ensure that tests pass -- if a field
            # is set to its default value, we don't write it out.
            if value:
                if key in self.fields and self.fields[key].is_set_on(self):
                    try:
                        xml.set(key, six.text_type(value))
                    except UnicodeDecodeError:
                        exception_message = format_xml_exception_message(self.location, key, value)
                        log.exception(exception_message)
                        # If exception is UnicodeDecodeError set value using unicode 'utf-8' scheme.
                        log.info("Setting xml value using 'utf-8' scheme.")
                        xml.set(key, six.text_type(value, 'utf-8'))
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

        transcripts = {}
        if self.transcripts is not None:
            transcripts.update(self.transcripts)

        edx_video_id = clean_video_id(self.edx_video_id)
        if edxval_api and edx_video_id:
            try:
                # Create static dir if not created earlier.
                resource_fs.makedirs(EXPORT_IMPORT_STATIC_DIR, recreate=True)

                # Backward compatible exports
                # edxval exports new transcripts into the course OLX and returns a transcript
                # files map so that it can also be rewritten in old transcript metadata fields
                # (i.e. `self.transcripts`) on import and older open-releases (<= ginkgo),
                # who do not have deprecated contentstore yet, can also import and use new-style
                # transcripts into their openedX instances.

                exported_metadata = edxval_api.export_to_xml(
                    video_id=edx_video_id,
                    resource_fs=resource_fs,
                    static_dir=EXPORT_IMPORT_STATIC_DIR,
                    course_id=six.text_type(self.runtime.course_id.for_branch(None))
                )
                # Update xml with edxval metadata
                xml.append(exported_metadata['xml'])

                # we don't need sub if english transcript
                # is also in new transcripts.
                new_transcripts = exported_metadata['transcripts']
                transcripts.update(new_transcripts)
                if new_transcripts.get('en'):
                    xml.set('sub', '')

                # Update `transcripts` attribute in the xml
                xml.set('transcripts', json.dumps(transcripts, sort_keys=True))

            except edxval_api.ValVideoNotFoundError:
                pass

            # Sorting transcripts for easy testing of resulting xml
            for transcript_language in sorted(transcripts.keys()):
                ele = etree.Element('transcript')
                ele.set('language', transcript_language)
                ele.set('src', transcripts[transcript_language])
                xml.append(ele)

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
            return u'https://www.youtube.com/watch?v={0}'.format(youtube_id)
        else:
            return u''

    def get_context(self):
        """
        Extend context by data for transcript basic tab.
        """
        _context = super(VideoBlock, self).get_context()

        metadata_fields = copy.deepcopy(self.editable_metadata_fields)

        display_name = metadata_fields['display_name']
        video_url = metadata_fields['html5_sources']
        video_id = metadata_fields['edx_video_id']
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
            'help': _('The URL for your video. This can be a YouTube URL or a link to an .mp4, .ogg, or '
                      '.webm video file hosted elsewhere on the Internet.'),
            'display_name': _('Default Video URL'),
            'field_name': 'video_url',
            'type': 'VideoList',
            'default_value': [get_youtube_link(youtube_id_1_0['default_value'])]
        })

        source_url = self.create_youtube_url(youtube_id_1_0['value'])
        # First try a lookup in VAL. If any video encoding is found given the video id then
        # override the source_url with it.
        if self.edx_video_id and edxval_api:

            val_profiles = ['youtube', 'desktop_webm', 'desktop_mp4']
            if HLSPlaybackEnabledFlag.feature_enabled(self.runtime.course_id.for_branch(None)):
                val_profiles.append('hls')

            # Get video encodings for val profiles.
            val_video_encodings = edxval_api.get_urls_for_profiles(self.edx_video_id, val_profiles)

            # VAL's youtube source has greater priority over external youtube source.
            if val_video_encodings.get('youtube'):
                source_url = self.create_youtube_url(val_video_encodings['youtube'])

            # If no youtube source is provided externally or in VAl, update source_url in order: hls > mp4 and webm
            if not source_url:
                if val_video_encodings.get('hls'):
                    source_url = val_video_encodings['hls']
                elif val_video_encodings.get('desktop_mp4'):
                    source_url = val_video_encodings['desktop_mp4']
                elif val_video_encodings.get('desktop_webm'):
                    source_url = val_video_encodings['desktop_webm']

        # Only add if html5 sources do not already contain source_url.
        if source_url and source_url not in video_url['value']:
            video_url['value'].insert(0, source_url)

        metadata = {
            'display_name': display_name,
            'video_url': video_url,
            'edx_video_id': video_id
        }
        _context.update({'transcripts_basic_tab_metadata': metadata})
        #### EOL ####
        eol_videolist = self.get_eol_videos_vimeo(self.course_id)
        _context['eol_videolist'] = {'data': eol_videolist, 'edx_video_id': self.edx_video_id}
        _context['course_id'] = str(self.course_id)
        #### EOL END ####
        return _context

    def get_eol_videos_vimeo(self, course_key):
        """
            EOL: Get a list of vimeo videos, only with status vimeo_encoding and upload_completed 
        """
        try:
            from eol_vimeo.models import EolVimeoVideo
            from eol_vimeo.vimeo_utils import update_video_vimeo
            from edxval.api import _get_video
            update_video_vimeo(str(course_key))
            video_list = []
            vimeo_list = EolVimeoVideo.objects.filter(course_key=course_key, status__in=['upload_completed', 'upload_completed_encoding']).values('edx_video_id')
            for video in vimeo_list:
                aux = _get_video(video['edx_video_id'])
                video_list.append({'edx_video_id': video['edx_video_id'], 'display_name': aux.client_video_id})
            return video_list
        except ImportError as e:
            log.error('EolVimeo - Error to import EolVimeoVideo or edxval.api._get_video, exception: {}'.format(str(e)))
            return []

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
    def parse_video_xml(cls, xml, id_generator=None):
        """
        Parse video fields out of xml_data. The fields are set if they are
        present in the XML.

        Arguments:
            id_generator is used to generate course-specific urls and identifiers
        """
        if isinstance(xml, six.string_types):
            xml = etree.fromstring(xml)

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
        if 'handout' in list(field_data.keys()) and course_id:
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

        # load license if it exists
        field_data = LicenseMixin.parse_license_from_xml(field_data, xml)

        return field_data

    def import_video_info_into_val(self, xml, resource_fs, course_id):
        """
        Import parsed video info from `xml` into edxval.

        Arguments:
            xml (lxml object): xml representation of video to be imported.
            resource_fs (OSFS): Import file system.
            course_id (str): course id
        """
        edx_video_id = clean_video_id(self.edx_video_id)

        # Create video_asset is not already present.
        video_asset_elem = xml.find('video_asset')
        if video_asset_elem is None:
            video_asset_elem = etree.Element('video_asset')

        # This will be a dict containing the list of names of the external transcripts.
        # Example:
        # {
        #     'en': ['The_Flash.srt', 'Harry_Potter.srt'],
        #     'es': ['Green_Arrow.srt']
        # }
        external_transcripts = defaultdict(list)

        # Add trancript from self.sub and self.youtube_id_1_0 fields.
        external_transcripts['en'] = [
            subs_filename(transcript, 'en')
            for transcript in [self.sub, self.youtube_id_1_0] if transcript
        ]

        for language_code, transcript in self.transcripts.items():
            external_transcripts[language_code].append(transcript)

        if edxval_api:
            edx_video_id = edxval_api.import_from_xml(
                video_asset_elem,
                edx_video_id,
                resource_fs,
                EXPORT_IMPORT_STATIC_DIR,
                external_transcripts,
                course_id=course_id
            )
        return edx_video_id

    def index_dictionary(self):
        xblock_body = super(VideoBlock, self).index_dictionary()
        video_body = {
            "display_name": self.display_name,
        }

        def _update_transcript_for_index(language=None):
            """ Find video transcript - if not found, don't update index """
            try:
                transcript = get_transcript(self, lang=language, output_format=Transcript.TXT)[0].replace("\n", " ")
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

    @classmethod
    @request_cached(
        request_cache_getter=lambda args, kwargs: args[1],
    )
    def get_cached_val_data_for_course(cls, request_cache, video_profile_names, course_id):
        """
        Returns the VAL data for the requested video profiles for the given course.
        """
        return edxval_api.get_video_info_for_course_and_profiles(six.text_type(course_id), video_profile_names)

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
        all_sources = self.html5_sources or []

        # Check in VAL data first if edx_video_id exists
        if self.edx_video_id:
            video_profile_names = context.get("profiles", ["mobile_low"])
            if HLSPlaybackEnabledFlag.feature_enabled(self.location.course_key) and 'hls' not in video_profile_names:
                video_profile_names.append('hls')

            # get and cache bulk VAL data for course
            val_course_data = self.get_cached_val_data_for_course(
                self.request_cache,
                video_profile_names,
                self.location.course_key,
            )
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
            if all_sources:
                encoded_videos["fallback"] = {
                    "url": all_sources[0],
                    "file_size": 0,  # File size is unknown for fallback URLs
                }

            # Include youtube link if there is no encoding for mobile- ie only a fallback URL or no encodings at all
            # We are including a fallback URL for older versions of the mobile app that don't handle Youtube urls
            if self.youtube_id_1_0:
                encoded_videos["youtube"] = {
                    "url": self.create_youtube_url(self.youtube_id_1_0),
                    "file_size": 0,  # File size is not relevant for external link
                }

        available_translations = self.available_translations(self.get_transcripts_info())
        transcripts = {
            lang: self.runtime.handler_url(self, 'transcript', 'download', query="lang=" + lang, thirdparty=True)
            for lang in available_translations
        }

        return {
            "only_on_web": self.only_on_web,
            "duration": val_video_data.get('duration', None),
            "transcripts": transcripts,
            "encoded_videos": encoded_videos,
            "all_sources": all_sources,
        }
