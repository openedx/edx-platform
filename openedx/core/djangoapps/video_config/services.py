"""
Video Configuration Service for XBlock runtime.

This service provides video-related configuration and feature flags
that are specific to the edx-platform implementation
for the extracted video block in xblocks-contrib repository.
"""

import logging

from opaque_keys.edx.keys import CourseKey, UsageKey
from xblocks_contrib.video.exceptions import TranscriptNotFoundError

from openedx.core.djangoapps.video_config import sharing
from organizations.api import get_course_organization
from openedx.core.djangoapps.video_config.models import (
    CourseYoutubeBlockedFlag,
    HLSPlaybackEnabledFlag,
)
from openedx.core.djangoapps.video_config.toggles import TRANSCRIPT_FEEDBACK
from openedx.core.djangoapps.video_pipeline.config.waffle import DEPRECATE_YOUTUBE
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError

log = logging.getLogger(__name__)


class VideoConfigService:
    """
    Service for providing video-related configuration and feature flags.

    This service abstracts away edx-platform specific functionality
    that the Video XBlock needs, allowing the Video XBlock to be
    extracted to a separate repository.
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

    def get_transcript_from_store(self, course_key, filename):
        """
        Return transcript from store by course key and filename.
        
        Args:
            course_key: Course key
            filename (str): filename of the asset
            
        Returns:
            Asset transcript from store
            
        Raises:
            TranscriptNotFoundError: If transcript not found
        """
        content_location = StaticContent.compute_location(course_key, filename)
        try:
            return contentstore().find(content_location)
        except NotFoundError as exc:
            raise TranscriptNotFoundError(
                f"Failed to get transcript: {exc}"
            ) from exc

    def delete_transcript_from_store(self, course_key, filename):
        """
        Delete transcript from store by course key and filename.
        
        Args:
            course_key: Course key
            filename (str): filename of the asset
            
        Returns:
            transcript location

        Raises:
            TranscriptNotFoundError: If transcript not found
        """
        try:
            content_location = StaticContent.compute_location(course_key, filename)
            contentstore().delete(content_location)
            log.info("Transcript asset %s was removed from store.", filename)
        except NotFoundError as exc:
            raise TranscriptNotFoundError(
                f"Failed to get transcript: {exc}"
            ) from exc
        return StaticContent.compute_location(course_key, filename)

    def find_transcript_from_store(self, course_key, filename):
        """
        Find transcript from store by course key and filename.
        
        Args:
            course_key: Course key
            filename (str): filename of the asset
            
        Returns:
            Transcript from store
            
        Raises:
            TranscriptNotFoundError: If asset not transcript
        """
        try:
            content_location = StaticContent.compute_location(course_key, filename)
            return contentstore().find(content_location).data.decode('utf-8')
        except NotFoundError as exc:
            raise TranscriptNotFoundError(
                f"Failed to get transcript: {exc}"
            ) from exc

    def save_transcript_into_store(self, content, filename, mime_type, course_key):
        """
        Save transcript into store by course key.
        
        Args:
            content: The content to save
            filename: The filename
            mime_type: The MIME type of the content
            course_key: The course key
            
        Returns:
            Content location of saved transcript in store
        """
        content_location = StaticContent.compute_location(course_key, filename)
        content = StaticContent(content_location, filename, mime_type, content)
        contentstore().save(content)
        return content_location
