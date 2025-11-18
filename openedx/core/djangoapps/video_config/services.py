"""
Video Configuration Service for XBlock runtime.

This service provides video-related configuration and feature flags
that are specific to the edx-platform implementation
for the extracted video block in xblocks-contrib repository.
"""

import logging

from opaque_keys.edx.keys import (
    CourseKey,
    UsageKey,
    UsageKeyV2,
)
from openedx.core.djangoapps.video_config import sharing
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

    def add_library_static_asset(self, usage_key: UsageKeyV2, filename: str, content: bytes) -> bool:
        """
        This method provides access to the library API for adding static assets
        to Learning Core components.
        """
        add_library_block_static_asset_file(
            usage_key,
            filename,
            content,
        )
        return True

    def delete_library_static_asset(self, usage_key: UsageKeyV2, filename: str) -> bool:
        """
        This method provides access to the library API for deleting static assets
        from Learning Core components.
        """
        delete_library_block_static_asset_file(
            usage_key,
            filename,
        )
        return True
