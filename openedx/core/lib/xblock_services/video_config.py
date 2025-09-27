"""
Video Configuration Service for XBlock runtime.

This service provides video-related configuration and feature flags
that are specific to the edx-platform implementation
for the extracted video block in xblocks-contrib repository.
"""

import logging
from typing import Optional, Dict, Any
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.video_config.models import HLSPlaybackEnabledFlag, CourseYoutubeBlockedFlag
from openedx.core.djangoapps.video_config.toggles import PUBLIC_VIDEO_SHARE, TRANSCRIPT_FEEDBACK
from openedx.core.djangoapps.video_pipeline.config.waffle import DEPRECATE_YOUTUBE
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag
from openedx.core.djangoapps.waffle_utils.models import WaffleFlagCourseOverrideModel


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

    def is_public_video_share_enabled(self, course_id: CourseKey) -> bool:
        """
        Check if public video sharing is enabled for the course.
        
        Args:
            course_id: The course key
            
        Returns:
            bool: True if public video sharing is enabled, False otherwise
        """
        return PUBLIC_VIDEO_SHARE.is_enabled(course_id)

    def is_transcript_feedback_enabled(self, course_id: CourseKey) -> bool:
        """
        Check if transcript feedback is enabled for the course.
        
        Args:
            course_id: The course key
            
        Returns:
            bool: True if transcript feedback is enabled, False otherwise
        """
        return TRANSCRIPT_FEEDBACK.is_enabled(course_id)

    def get_branding_info(self) -> Dict[str, Any]:
        """
        Get branding information for the course.
        
        Returns:
            Dict[str, Any]: Branding information
        """
        try:
            from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag
            from openedx.core.djangoapps.waffle_utils.models import WaffleFlagCourseOverrideModel

            # TODO: Study how to access BrandingInfoConfig from edx-platform
            # This is a placeholder implementation
            # branding_info = BrandingInfoConfig.get_config().get(user_location)
            return {
                'logo_url': None,
                'logo_alt_text': None,
                'favicon_url': None
            }
        except ImportError:
            log.warning("Could not import branding config, returning default values")
            return {
                'logo_url': None,
                'logo_alt_text': None,
                'favicon_url': None
            }

    def get_course_by_id(self, course_id: CourseKey):
        """
        Get course information by course ID.
        
        Args:
            course_id: The course key
            
        Returns:
            Course object or None
        """
        try:
            from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

            # TODO: Study how to access get_course_by_id from edx-platform
            # This is a placeholder implementation
            # course = get_course_by_id(self.context_key)
            # return getattr(course, 'video_sharing_options', None)
            return None
        except ImportError:
            log.warning("Could not import course models, returning None")
            return None

    def get_course_organization(self, course_id: CourseKey) -> Optional[str]:
        """
        Get the organization for a course.
        
        Args:
            course_id: The course key
            
        Returns:
            Organization string or None
        """
        try:
            from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

            # TODO: Study how to access course organization from edx-platform
            # This is a placeholder implementation
            # organization = get_course_organization(self.course_id)
            # template_context['sharing_sites_info'] = sharing_sites_info_for_video(
            #     public_video_url,
            #     organization=organization
            # )
            return None
        except ImportError:
            log.warning("Could not import course models, returning None")
            return None
