"""
Video Configuration Service for XBlock runtime.

This service provides video-related configuration and feature flags
that are specific to the edx-platform implementation
for the extracted video block in xblocks-contrib repository.
"""

import logging

from opaque_keys.edx.keys import CourseKey, UsageKeyV2
from organizations.api import get_course_organization

from openedx.core.djangoapps.video_config.models import (
    CourseYoutubeBlockedFlag,
    HLSPlaybackEnabledFlag,
)
from openedx.core.djangoapps.video_config.toggles import TRANSCRIPT_FEEDBACK
from openedx.core.djangoapps.video_config.utils import VideoSharingUtils
from openedx.core.djangoapps.video_pipeline.config.waffle import DEPRECATE_YOUTUBE


log = logging.getLogger(__name__)


class VideoConfigService:
    """
    Service for providing video-related configuration and feature flags.

    This service abstracts away edx-platform specific functionality
    that the Video XBlock needs, allowing the Video XBlock to be
    extracted to a separate repository.
    """

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

        if not VideoSharingUtils.is_public_sharing_enabled(video_block):
            return context

        public_video_url = VideoSharingUtils.get_public_video_url(video_block)
        context['public_sharing_enabled'] = True
        context['public_video_url'] = public_video_url

        organization = get_course_organization(course_id)

        # Import here to avoid circular dependency
        from xmodule.video_block.sharing_sites import sharing_sites_info_for_video
        sharing_sites_info = sharing_sites_info_for_video(
            public_video_url,
            organization=organization
        )
        context['sharing_sites_info'] = sharing_sites_info

        return context

    def is_hls_playback_enabled(self, course_id: CourseKey) -> bool:
        """
        Check if HLS playback is enabled for the course.
        """
        return HLSPlaybackEnabledFlag.feature_enabled(course_id)

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

    def is_transcript_feedback_enabled(self, course_id: CourseKey) -> bool:
        """
        Check if transcript feedback is enabled for the course.
        """
        return TRANSCRIPT_FEEDBACK.is_enabled(course_id)

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
        # Import here to avoid circular dependency
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
        # Import here to avoid circular dependency
        from openedx.core.djangoapps.content_libraries.api import lib_api
        lib_api.delete_library_block_static_asset_file(
            usage_key,
            filename,
        )
        return True

    def get_transcript_from_store(self, course_key, filename):
        """
        Return transcript from store by course key and filename.
        
        Args:
            course_key: Course key
            filename (str): filename of the asset
            
        Returns:
            Asset data from store
            
        Raises:
            NotFoundError: If asset not found
        """
        # Import here to avoid circular dependency
        from xmodule.video_block.transcripts_utils import Transcript
        return Transcript.get_asset_by_course_key(course_key, filename)

    def delete_transcript_from_store(self, course_key, filename):
        """
        Delete transcript from store by course key and filename.
        
        Args:
            course_key: Course key
            filename (str): filename of the asset
            
        Returns:
            Asset location
        """
        # Import here to avoid circular dependency
        from xmodule.video_block.transcripts_utils import Transcript
        return Transcript.delete_asset_by_course_key(course_key, filename)

    def find_transcript_from_store(self, course_key, filename):
        """
        Find transcript from store by course key and filename.
        
        Args:
            course_key: Course key
            filename (str): filename of the asset
            
        Returns:
            Asset from store
            
        Raises:
            NotFoundError: If asset not found
        """
        # Import here to avoid circular dependency
        from xmodule.video_block.transcripts_utils import Transcript
        return Transcript.find_asset(course_key, filename)

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
        # Import here to avoid circular dependency
        from xmodule.video_block.transcripts_utils import Transcript
        return Transcript.save_transcript(content, filename, mime_type, course_key)

    def get_transcript(self, video_block, lang=None, output_format='srt', youtube_id=None):
        """
        Get video transcript from edx-val, content store, or learning core.
        
        This method delegates to the platform's transcript utilities which handle
        multiple transcript sources: edx-val (video transcripts), contentstore 
        (MongoDB GridFS), and Learning Core (for content libraries).
        
        Arguments:
            video_block (Video block): Video block instance
            lang (unicode): transcript language code (e.g., 'en', 'es')
            output_format (unicode): transcript output format ('srt', 'sjson', or 'txt')
            youtube_id (unicode): youtube video id (optional, for speed-specific transcripts)
            
        Returns:
            tuple: (content, filename, mimetype)
                - content: The transcript content in the requested format
                - filename: Suggested filename for the transcript
                - mimetype: MIME type string for the format
                
        Raises:
            NotFoundError: If transcript cannot be found or retrieved
        """
        # Import here to avoid circular dependency
        from xmodule.video_block.transcripts_utils import get_transcript
        return get_transcript(video_block, lang, output_format, youtube_id)
