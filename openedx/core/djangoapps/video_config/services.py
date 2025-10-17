"""
Video Configuration Service for XBlock runtime.

This service provides video-related configuration and feature flags
that are specific to the edx-platform implementation
for the extracted video block in xblocks-contrib repository.
"""

import logging

from opaque_keys.edx.keys import CourseKey, UsageKey

from openedx.core.djangoapps.video_config.utils import VideoSharingUtils
from organizations.api import get_course_organization


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
        return VideoSharingUtils.get_public_video_url(usage_id)

    def get_public_sharing_context(self, video_block, course_key: CourseKey) -> dict:
        """
        Get the complete public sharing context for a video.

        Args:
            video_block: The video XBlock instance
            course_id: The course identifier

        Returns:
            dict: Context dictionary with sharing information, empty if sharing is disabled
        """
        context = {}

        if not VideoSharingUtils.is_public_sharing_enabled(video_block):
            return context

        public_video_url = VideoSharingUtils.get_public_video_url(video_block.location)
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
