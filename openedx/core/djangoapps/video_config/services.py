"""
Video Configuration Service for XBlock runtime.

This service provides video-related configuration and feature flags
that are specific to the edx-platform implementation
for the extracted video block in xblocks-contrib repository.
"""

import logging

from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2
from xblocks_contrib.video.exceptions import TranscriptNotFoundError

from openedx.core.djangoapps.video_config import sharing
from django.core.files import File
from django.core.files.base import ContentFile
from edxval.api import create_external_video, create_or_update_video_transcript, delete_video_transcript
from organizations.api import get_course_organization
from openedx.core.djangoapps.video_config.models import (
    CourseYoutubeBlockedFlag,
    HLSPlaybackEnabledFlag,
)
from openedx.core.djangoapps.video_config.toggles import TRANSCRIPT_FEEDBACK
from openedx.core.djangoapps.video_pipeline.config.waffle import DEPRECATE_YOUTUBE
from openedx.core.djangoapps.content_libraries.api import (
    add_library_block_static_asset_file,
    delete_library_block_static_asset_file,
)
from openedx.core.djangoapps.video_config.transcripts_utils import (
    Transcript,
    clean_video_id,
    get_html5_ids,
    remove_subs_from_store,
)

log = logging.getLogger(__name__)


class VideoConfigService:
    """
    Service for providing video-related configuration and feature flags.

    This service abstracts away edx-platform specific functionality
    that the Video XBlock needs, allowing the Video XBlock to be
    extracted to a separate repository.

    TODO: This service could be improved in a few ways:
    https://github.com/openedx/edx-platform/issues/37656
    """

    def get_public_video_url(self, usage_id: UsageKey) -> str:
        """
        Returns the public video url
        """
        return sharing.get_public_video_url(usage_id)

    def get_public_sharing_context(self, video_block, course_key: CourseKey) -> dict:
        """
        Get the complete public sharing context for a video.

        Args:
            video_block: The video XBlock instance
            course_key: The course identifier

        Returns:
            dict: Context dictionary with sharing information, empty if sharing is disabled
        """
        context = {}

        if not sharing.is_public_sharing_enabled(video_block.location, video_block.public_access):
            return context

        public_video_url = sharing.get_public_video_url(video_block.location)
        context['public_sharing_enabled'] = True
        context['public_video_url'] = public_video_url

        organization = get_course_organization(course_key)

        from openedx.core.djangoapps.video_config.sharing_sites import sharing_sites_info_for_video
        sharing_sites_info = sharing_sites_info_for_video(
            public_video_url,
            organization=organization
        )
        context['sharing_sites_info'] = sharing_sites_info

        return context

    def is_transcript_feedback_enabled(self, course_id: CourseKey) -> bool:
        """
        Check if transcript feedback is enabled for the course.
        """
        return TRANSCRIPT_FEEDBACK.is_enabled(course_id)

    def is_youtube_deprecated(self, course_id: CourseKey) -> bool:
        """
        Check if YouTube is deprecated for the course.
        """
        return DEPRECATE_YOUTUBE.is_enabled(course_id)

    def is_youtube_blocked_for_course(self, course_id: CourseKey) -> bool:
        """
        Check if YouTube is blocked for the course.
        """
        return CourseYoutubeBlockedFlag.feature_enabled(course_id)

    def is_hls_playback_enabled(self, course_id: CourseKey) -> bool:
        """
        Check if HLS playback is enabled for the course.
        """
        return HLSPlaybackEnabledFlag.feature_enabled(course_id)

    def get_transcript(
        self,
        video_block,
        lang: str | None = None,
        output_format: str = 'srt',
        youtube_id: str | None = None,
    ) -> tuple[bytes, str, str]:
        """
        Retrieve a transcript from the runtime's storage.

        Returns:
            tuple(bytes, str, str): transcript content, filename, and mimetype.

        Raises:
            TranscriptsGenerationException: If the transcript cannot be found or retrieved
            TranscriptNotFoundError: If the transcript cannot be found or retrieved
        """
        # Import here to avoid circular dependency
        from openedx.core.djangoapps.video_config.transcripts_utils import get_transcript
        from xmodule.exceptions import NotFoundError

        try:
            return get_transcript(video_block, lang, output_format, youtube_id)
        except NotFoundError as exc:
            raise TranscriptNotFoundError(
                f"Failed to get transcript: {exc}"
            ) from exc

    def upload_transcript(
        self,
        *,
        video_block,
        language_code: str,
        new_language_code: str | None,
        transcript_file: File,
        edx_video_id: str | None,
    ) -> None:
        """
        Store a transcript, however the runtime prefers to.

        Mutates:
        * video_block.transcripts
        * video_block.edx_video_id, iff a new video is created in edx-val.

        Can raise:
        * UnicodeDecodeError
        * TranscriptsGenerationException
        """
        is_library = isinstance(video_block.usage_key.context_key, LibraryLocatorV2)
        content: bytes = transcript_file.read()
        if is_library:
            # Save transcript as static asset in Learning Core if is a library component
            filename = f'static/transcript-{new_language_code}.srt'
            add_library_block_static_asset_file(video_block.usage_key, filename, content)
        else:
            edx_video_id = clean_video_id(edx_video_id)
            if not edx_video_id:
                # Back-populate the video ID for an external video.
                # pylint: disable=attribute-defined-outside-init
                edx_video_id = create_external_video(display_name='external video')
                video_block.edx_video_id = edx_video_id
            filename = f'{edx_video_id}-{new_language_code}.srt'
            # Convert SRT transcript into an SJSON format and upload it to S3 if a course component
            sjson_subs = Transcript.convert(
                content=content.decode('utf-8'),
                input_format=Transcript.SRT,
                output_format=Transcript.SJSON
            ).encode()
            create_or_update_video_transcript(
                video_id=edx_video_id,
                language_code=language_code,
                metadata={
                    'file_format': Transcript.SJSON,
                    'language_code': new_language_code,
                },
                file_data=ContentFile(sjson_subs),
            )

        # If a new transcript is added, then both new_language_code and
        # language_code fields will have the same value.
        if language_code != new_language_code:
            video_block.transcripts.pop(language_code, None)
        video_block.transcripts[new_language_code] = filename

        if is_library:
            _save_transcript_field(video_block)

    def delete_transcript(
        self,
        *,
        video_block,
        edx_video_id: str | None,
        language_code: str,
    ) -> None:
        """
        Delete a transcript from the runtime's storage.
        """
        edx_video_id = clean_video_id(edx_video_id)
        if edx_video_id:
            delete_video_transcript(video_id=edx_video_id, language_code=language_code)
        if isinstance(video_block.context_key, LibraryLocatorV2):
            transcript_name = video_block.transcripts.pop(language_code, None)
            if transcript_name:
                delete_library_block_static_asset_file(video_block.usage_key, f"static/{transcript_name}")
                _save_transcript_field(video_block)
        else:
            if language_code == 'en':
                # remove any transcript file from content store for the video ids
                possible_sub_ids = [
                    video_block.sub,  # pylint: disable=access-member-before-definition
                    video_block.youtube_id_1_0
                ] + get_html5_ids(video_block.html5_sources)
                for sub_id in possible_sub_ids:
                    remove_subs_from_store(sub_id, video_block, language_code)
                # update metadata as `en` can also be present in `transcripts` field
                remove_subs_from_store(
                    video_block.transcripts.pop(language_code, None), video_block, language_code
                )
                # also empty `sub` field
                video_block.sub = ''  # pylint: disable=attribute-defined-outside-init
            else:
                remove_subs_from_store(
                    video_block.transcripts.pop(language_code, None), video_block, language_code
                )


def _save_transcript_field(video_block):
    """
    Hacky workaround to ensure that transcript field is saved for Learning Core video blocks.

    It's not clear why this is necessary.
    """
    field = video_block.fields['transcripts']
    if video_block.transcripts:
        transcripts_copy = video_block.transcripts.copy()
        # Need to delete to overwrite, it's weird behavior,
        # but it only works like this.
        field.delete_from(video_block)
        field.write_to(video_block, transcripts_copy)
    else:
        field.delete_from(video_block)
