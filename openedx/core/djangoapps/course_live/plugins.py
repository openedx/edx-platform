"""
Course app configuration for live.
"""
from typing import Dict, Optional

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_noop as _
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_apps.plugins import CourseApp
from openedx.core.djangoapps.course_live.config.waffle import ENABLE_COURSE_LIVE

from .models import CourseLiveConfiguration

User = get_user_model()


class LiveCourseApp(CourseApp):
    """
    Course App config for Live.
    """

    app_id = "live"
    name = _("Live")
    description = _("Enable in-platform video conferencing by configuring live")
    documentation_links = {
        # TODO: add the actual documentation link once it exists
        "learn_more_configuration": '',
    }

    @classmethod
    def is_available(cls, course_key: CourseKey) -> bool:
        """
        Live is available based on ENABLE_COURSE_LIVE flag
        """
        return ENABLE_COURSE_LIVE.is_enabled(course_key)

    @classmethod
    def is_enabled(cls, course_key: CourseKey) -> bool:
        """
        Live enable/disable status is stored in a separate model.
        """
        return CourseLiveConfiguration.is_enabled(course_key)

    @classmethod
    def set_enabled(cls, course_key: CourseKey, enabled: bool, user: 'User') -> bool:
        """
        Set live enabled status in CourseLiveConfiguration model.
        """
        configuration = CourseLiveConfiguration.get(course_key)
        if configuration is None:
            raise ValueError("Can't enable/disable live for course before it is configured.")
        configuration.enabled = enabled
        configuration.save()
        return configuration.enabled

    @classmethod
    def get_allowed_operations(cls, course_key: CourseKey, user: Optional[User] = None) -> Dict[str, bool]:
        """
        Return allowed operations for live app.
        """
        # Can only enable live for a course if live is configured.
        can_enable = CourseLiveConfiguration.get(course_key) is not None
        return {
            "enable": can_enable,
            "configure": True,
        }
