"""
Platform plugins to support a verified upgrade tool.
"""


import datetime

import pytz
from crum import get_current_request
from django.conf import settings
from django.utils.translation import ugettext as _
from django.urls import reverse
from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.courseware.utils import verified_upgrade_deadline_link
from openedx.features.course_experience.course_tools import CourseTool
from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


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


class FinancialAssistanceTool(CourseTool):
    """
    The financial assistance tool.
    """
    @classmethod
    def analytics_id(cls):
        """
        Returns an id to uniquely identify this tool in analytics events.
        """
        return 'edx.tool.financial_assistance'

    @classmethod
    def is_enabled(cls, request, course_key):
        """
        Show this link for active courses where financial assistance is available, unless upgrade deadline has passed
        """
        now = datetime.datetime.now(pytz.UTC)
        feature_flags = None
        try:
            course_overview = CourseOverview.objects.get(id=course_key)
        except CourseOverview.DoesNotExist:
            course_overview = None

        # hide link if there's no ENABLE_FINANCIAL_ASSISTANCE_FORM setting (ex: Edge) or if it's False
        subset_name = 'FEATURES'
        feature_flags = getattr(settings, subset_name)
        if feature_flags is None or not feature_flags.get('ENABLE_FINANCIAL_ASSISTANCE_FORM'):
            return False

        # hide link for archived courses
        if course_overview is not None and course_overview.end_date is not None and now > course_overview.end_date:
            return False

        # hide link if not logged in or user not enrolled in the course
        if not request.user or not CourseEnrollment.is_enrolled(request.user, course_key):
            return False

        enrollment = CourseEnrollment.get_enrollment(request.user, course_key)

        # hide if we're no longer in an upsell mode (already upgraded)
        if enrollment.mode not in CourseMode.UPSELL_TO_VERIFIED_MODES:
            return False

        # hide if there's no course_upgrade_deadline, or one with a value in the past
        if enrollment.course_upgrade_deadline:
            if now > enrollment.course_upgrade_deadline:
                return False
        else:
            return False

        return bool(course_overview.eligible_for_financial_aid)

    @classmethod
    def title(cls, course_key=None):
        """
        Returns the title of this tool.
        """
        return _('Financial Assistance')

    @classmethod
    def icon_classes(cls, course_key=None):
        """
        Returns the icon classes needed to represent this tool.
        """
        return 'fa fa-info'

    @classmethod
    def url(cls, course_key):
        """
        Returns the URL for this tool for the specified course key.
        """
        return reverse('financial_assistance')
