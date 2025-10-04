"""
Video Configuration Service for XBlock runtime.

This service provides video-related configuration and feature flags
that are specific to the edx-platform implementation
for the extracted video block in xblocks-contrib repository.
"""

import logging
from typing import Optional

from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.keys import UsageKeyV2

from openedx.core.djangoapps.video_config.models import (
    CourseYoutubeBlockedFlag,
    HLSPlaybackEnabledFlag,
)
from openedx.core.djangoapps.video_config.toggles import TRANSCRIPT_FEEDBACK
from openedx.core.djangoapps.video_pipeline.config.waffle import DEPRECATE_YOUTUBE
from xmodule.exceptions import NotFoundError
from openedx.core.lib.xblock_services.video_config_utils import (
    get_public_video_url,
    is_public_sharing_enabled,
)
from organizations.api import get_course_organization


log = logging.getLogger(__name__)


class VideoConfigService:
    """
    Service for providing video-related configuration and feature flags.

    This service abstracts away edx-platform specific functionality
    that the Video XBlock needs, allowing the Video XBlock to be
    extracted to a separate repository.
    """

    def __init__(self, course_id: Optional[CourseKey] = None):
        """
        Initialize the VideoConfigService.

        Args:
            course_id: The course key for course-specific configurations
        """
        self.course_id = course_id

    def is_hls_playback_enabled(self, course_id) -> bool:
        """
        Check if HLS playback is enabled for the course.

        Arguments:
            course_id (CourseKey): course id for whom feature will be checked.

        Returns:
            bool: True if HLS playback is enabled, False otherwise
        """
        return HLSPlaybackEnabledFlag.feature_enabled(course_id)

    def is_youtube_deprecated(self, course_id: CourseKey) -> bool:
        """
        Check if YouTube is deprecated for the course.

        Args:
            course_id: The course key

        Returns:
            bool: True if YouTube is deprecated, False otherwise
        """
        return DEPRECATE_YOUTUBE.is_enabled(course_id)

    def is_youtube_blocked_for_course(self, course_id: CourseKey) -> bool:
        """
        Check if YouTube is blocked for the course.

        Args:
            course_id: The course key

        Returns:
            bool: True if YouTube is blocked, False otherwise
        """
        return CourseYoutubeBlockedFlag.feature_enabled(course_id)

    def is_transcript_feedback_enabled(self, course_id: CourseKey) -> bool:
        """
        Check if transcript feedback is enabled for the course.

        Args:
            course_id: The course key

        Returns:
            bool: True if transcript feedback is enabled, False otherwise
        """
        return TRANSCRIPT_FEEDBACK.is_enabled(course_id)

    def get_public_sharing_context(self, video_block, course_id):
        """
        Get the complete public sharing context for a video.

        Args:
            video_block: The video XBlock instance
            course_id: The course identifier

        Returns:
            dict: Context dictionary with sharing information, empty if sharing is disabled
        """
        context = {}

        if not is_public_sharing_enabled(video_block):
            return context

        public_video_url = get_public_video_url(video_block)
        context['public_sharing_enabled'] = True
        context['public_video_url'] = public_video_url

        organization = get_course_organization(self.course_id)

        from xmodule.video_block.sharing_sites import sharing_sites_info_for_video
        sharing_sites_info = sharing_sites_info_for_video(
            public_video_url,
            organization=organization
        )
        context['sharing_sites_info'] = sharing_sites_info

        return context

    def get_component_version(self, usage_key: UsageKeyV2):
        """
        Get the component version for a given usage key.

        Args:
            usage_key: The usage key for the XBlock component

        Returns:
            ComponentVersion: The draft version of the component

        Raises:
            NotFoundError: If the component was soft-deleted or doesn't exist
        """
        from openedx.core.djangoapps.xblock.api import get_component_from_usage_key
        component = get_component_from_usage_key(usage_key)
        component_version = component.versioning.draft
        if not component_version:
            raise NotFoundError(
                f"No component version for {usage_key} because Component {component.uuid} "
                "was soft-deleted."
            )
        return component_version

    def get_youtube_metadata(self, video_id: str, request):
        """
        Get YouTube metadata for a given video ID.

        Args:
            video_id: The YouTube video ID
            request: The HTTP request object

        Returns:
            tuple: (metadata_dict, status_code)
        """
        from lms.djangoapps.courseware.views.views import load_metadata_from_youtube
        metadata, status_code = load_metadata_from_youtube(video_id=video_id, request=request)
        return metadata, status_code

    def add_library_static_asset(self, usage_key: UsageKeyV2, filename: str, content: bytes):
        """
        Add a static asset file to a library component.

        This method provides access to the library API for adding static assets
        to Learning Core components.

        Args:
            usage_key: The usage key for the XBlock component
            filename: The filename for the asset
            content: The binary content of the asset

        Returns:
            bool: True if successful, False otherwise
        """
        from openedx.core.djangoapps.content_libraries.api import lib_api
        lib_api.add_library_block_static_asset_file(
            usage_key,
            filename,
            content,
        )
        return True

    def delete_library_static_asset(self, usage_key: UsageKeyV2, filename: str):
        """
        Delete a static asset file from a library component.

        This method provides access to the library API for deleting static assets
        from Learning Core components.

        Args:
            usage_key: The usage key for the XBlock component
            filename: The filename of the asset to delete

        Returns:
            bool: True if successful, False otherwise
        """
        from openedx.core.djangoapps.content_libraries.api import lib_api
        lib_api.delete_library_block_static_asset_file(
            usage_key,
            filename,
        )
        return True
