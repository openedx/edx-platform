"""
Video configuration utilities for XBlock runtime.

This module provides utility functions for video-related configuration
that are specific to the edx-platform implementation.
"""

import logging

from django.conf import settings

from openedx.core.djangoapps.video_config.toggles import PUBLIC_VIDEO_SHARE
from openedx.core.lib.courses import get_course_by_id
from xmodule.course_block import (
    COURSE_VIDEO_SHARING_ALL_VIDEOS,
    COURSE_VIDEO_SHARING_NONE,
)

log = logging.getLogger(__name__)


def get_public_video_url(video_block):
    """
    Returns the public video url
    """
    return fr'{settings.LMS_ROOT_URL}/videos/{str(video_block.location)}'


def is_public_sharing_enabled(video_block):
    """
    Check if public sharing is enabled for a video.

    Args:
        video_block: The video XBlock instance

    Returns:
        bool: True if public sharing is enabled, False otherwise
    """
    if not video_block.context_key.is_course:
        return False  # Only courses support this feature (not libraries)

    try:
        # Video share feature must be enabled for sharing settings to take effect
        feature_enabled = PUBLIC_VIDEO_SHARE.is_enabled(video_block.context_key)
    except Exception as err:  # pylint: disable=broad-except
        log.exception(f"Error retrieving course for course ID: {video_block.context_key}")
        return False

    if not feature_enabled:
        return False

    # Check if the course specifies a general setting
    course_video_sharing_option = get_course_video_sharing_override(video_block)

    # Course can override all videos to be shared
    if course_video_sharing_option == COURSE_VIDEO_SHARING_ALL_VIDEOS:
        return True

    # ... or no videos to be shared
    elif course_video_sharing_option == COURSE_VIDEO_SHARING_NONE:
        return False

    # ... or can fall back to per-video setting
    # Equivalent to COURSE_VIDEO_SHARING_PER_VIDEO or None / unset
    else:
        return video_block.public_access


def get_course_video_sharing_override(video_block):
    """
    Return course video sharing options override or None

    Args:
        video_block: The video XBlock instance

    Returns:
        Course video sharing option or None
    """
    if not video_block.context_key.is_course:
        return False  # Only courses support this feature (not libraries)

    try:
        course = get_course_by_id(video_block.context_key)
        return getattr(course, 'video_sharing_options', None)
    except Exception as err:  # pylint: disable=broad-except
        log.exception(f"Error retrieving course for course ID: {video_block.course_id}")
        return None
