"""
Unit tests for video-related REST APIs.
"""


import csv
import json
import re
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
from unittest.mock import Mock, patch

import dateutil.parser
import ddt
import pytz
from django.conf import settings
from django.test.utils import override_settings
from edx_toggles.toggles.testutils import override_waffle_flag, override_waffle_switch
from edxval.api import (
    create_or_update_transcript_preferences,
    create_or_update_video_transcript,
    create_profile,
    create_video,
    get_course_video_image_url,
    get_transcript_preferences,
    get_video_info
)

from cms.djangoapps.contentstore.models import VideoUploadConfig
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.utils import reverse_course_url
from openedx.core.djangoapps.profile_images.tests.helpers import make_image_file
from openedx.core.djangoapps.video_pipeline.config.waffle import (
    DEPRECATE_YOUTUBE,
    ENABLE_DEVSTACK_VIDEO_UPLOADS,
)
from openedx.core.djangoapps.waffle_utils.models import WaffleFlagCourseOverrideModel
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order

from ..videos import (
    ENABLE_VIDEO_UPLOAD_PAGINATION,
    KEY_EXPIRATION_IN_SECONDS,
    VIDEO_IMAGE_UPLOAD_ENABLED,
    PUBLIC_VIDEO_SHARE,
    StatusDisplayStrings,
    TranscriptProvider,
    _get_default_video_image_url,
    convert_video_status
)


class VideoUploadTestBase:
    """
    Test cases for the video upload feature
    """

    def get_url_for_course_key(self, course_key, kwargs=None):
        """Return video handler URL for the given course"""
        return reverse_course_url(self.VIEW_NAME, course_key, kwargs)  # lint-amnesty, pylint: disable=no-member

    def setUp(self):
        super().setUp()  # lint-amnesty, pylint: disable=no-member
        self.url = self.get_url_for_course_key(self.course.id)
        self.test_token = "test_token"
        self.course.video_upload_pipeline = {
            "course_video_upload_token": self.test_token,
        }
        self.save_course()  # lint-amnesty, pylint: disable=no-member
