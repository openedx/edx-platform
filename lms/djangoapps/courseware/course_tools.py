"""
Platform plugins to support a verified upgrade tool.
"""

import datetime
import pytz
from crum import get_current_request
from django.utils.translation import ugettext as _

from openedx.core.djangoapps.course_modes.models import CourseMode
from openedx.features.course_experience.course_tools import CourseTool
from student.models import CourseEnrollment
from courseware.date_summary import verified_upgrade_deadline_link


class VerifiedUpgradeTool(CourseTool):
    """
    The verified upgrade tool.
    """
    @classmethod
    def analytics_id(cls):
        """
        Returns an id to uniquely identify this tool in analytics events.
        """
        return 'edx.tool.verified_upgrade'

    @classmethod
    def is_enabled(cls, request, course_key):
        """
        Show this tool to all learners who are eligible to upgrade.
        """
        enrollment = CourseEnrollment.get_enrollment(request.user, course_key)
        if enrollment is None:
            return False

        if enrollment.dynamic_upgrade_deadline is None:
            return False

        if not enrollment.is_active:
            return False

        if enrollment.mode not in CourseMode.UPSELL_TO_VERIFIED_MODES:
            return False

        if enrollment.course_upgrade_deadline is None:
            return False

        if datetime.datetime.now(pytz.UTC) >= enrollment.course_upgrade_deadline:
            return False

        return True

    @classmethod
    def title(cls):
        """
        Returns the title of this tool.
        """
        return _('Upgrade to Verified')

    @classmethod
    def icon_classes(cls):
        """
        Returns the icon classes needed to represent this tool.
        """
        return 'fa fa-certificate'

    @classmethod
    def url(cls, course_key):
        """
        Returns the URL for this tool for the specified course key.
        """
        request = get_current_request()
        return verified_upgrade_deadline_link(request.user, course_id=course_key)
