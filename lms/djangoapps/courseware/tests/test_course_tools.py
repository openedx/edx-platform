"""
Unit tests for course tools.
"""


import datetime

import crum
import pytz
from django.test import RequestFactory
from mock import patch

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.courseware.course_tools import FinancialAssistanceTool, VerifiedUpgradeTool
from lms.djangoapps.courseware.models import DynamicUpgradeDeadlineConfiguration
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.schedules.config import CREATE_SCHEDULE_WAFFLE_FLAG
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class VerifiedUpgradeToolTest(SharedModuleStoreTestCase):

    @classmethod
    def setUpClass(cls):
        super(VerifiedUpgradeToolTest, cls).setUpClass()
        cls.now = datetime.datetime.now(pytz.UTC)

        cls.course = CourseFactory.create(
            org='edX',
            number='test',
            display_name='Test Course',
            self_paced=True,
            start=cls.now - datetime.timedelta(days=30),
        )
        cls.course_overview = CourseOverview.get_from_id(cls.course.id)

    @override_waffle_flag(CREATE_SCHEDULE_WAFFLE_FLAG, True)
    def setUp(self):
        super(VerifiedUpgradeToolTest, self).setUp()

        self.course_verified_mode = CourseModeFactory(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=self.now + datetime.timedelta(days=30),
        )

        patcher = patch('openedx.core.djangoapps.schedules.signals.get_current_site')
        mock_get_current_site = patcher.start()
        self.addCleanup(patcher.stop)
        mock_get_current_site.return_value = SiteFactory.create()

        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)

        self.request = RequestFactory().request()
        crum.set_current_request(self.request)
        self.addCleanup(crum.set_current_request, None)
        self.enrollment = CourseEnrollmentFactory(
            course_id=self.course.id,
            mode=CourseMode.AUDIT,
            course=self.course_overview,
        )
        self.request.user = self.enrollment.user

    def test_tool_visible(self):
        self.assertTrue(VerifiedUpgradeTool().is_enabled(self.request, self.course.id))

    def test_not_visible_when_no_enrollment_exists(self):
        self.enrollment.delete()

        request = RequestFactory().request()
        request.user = UserFactory()
        self.assertFalse(VerifiedUpgradeTool().is_enabled(self.request, self.course.id))

    def test_not_visible_when_using_deadline_from_course_mode(self):
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=False)
        self.assertFalse(VerifiedUpgradeTool().is_enabled(self.request, self.course.id))

    def test_not_visible_when_enrollment_is_inactive(self):
        self.enrollment.is_active = False
        self.enrollment.save()
        self.assertFalse(VerifiedUpgradeTool().is_enabled(self.request, self.course.id))

    def test_not_visible_when_already_verified(self):
        self.enrollment.mode = CourseMode.VERIFIED
        self.enrollment.save()
        self.assertFalse(VerifiedUpgradeTool().is_enabled(self.request, self.course.id))

    def test_not_visible_when_no_verified_track(self):
        self.course_verified_mode.delete()
        self.assertFalse(VerifiedUpgradeTool().is_enabled(self.request, self.course.id))

    def test_not_visible_when_course_deadline_has_passed(self):
        self.course_verified_mode.expiration_datetime = self.now - datetime.timedelta(days=1)
        self.course_verified_mode.save()
        self.assertFalse(VerifiedUpgradeTool().is_enabled(self.request, self.course.id))

    def test_not_visible_when_course_mode_has_no_deadline(self):
        self.course_verified_mode.expiration_datetime = None
        self.course_verified_mode.save()
        self.assertFalse(VerifiedUpgradeTool().is_enabled(self.request, self.course.id))


class FinancialAssistanceToolTest(SharedModuleStoreTestCase):
    """
    Tests for FinancialAssistanceTool
    """
    @classmethod
    def setUpClass(cls):
        super(FinancialAssistanceToolTest, cls).setUpClass()
        cls.now = datetime.datetime.now(pytz.UTC)

        cls.course = CourseFactory.create(
            org='edX',
            number='test',
            display_name='Test Course',
            self_paced=True,
        )
        cls.course_overview = CourseOverview.get_from_id(cls.course.id)

    @override_waffle_flag(CREATE_SCHEDULE_WAFFLE_FLAG, True)
    def setUp(self):
        super(FinancialAssistanceToolTest, self).setUp()

        self.course_financial_mode = CourseModeFactory(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=self.now + datetime.timedelta(days=1),
        )
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)

        self.request = RequestFactory().request()
        crum.set_current_request(self.request)
        self.addCleanup(crum.set_current_request, None)

        # baseline course enrollment, future upgrade deadline
        self.enrollment = CourseEnrollmentFactory(
            course_id=self.course.id,
            mode=CourseMode.AUDIT,
            course=self.course_overview,
        )
        self.request.user = self.enrollment.user

        # enrollment where learner has upgraded
        self.enrollment_upgraded = CourseEnrollmentFactory(
            course_id=self.course.id,
            mode=CourseMode.VERIFIED,
            course=self.course_overview,
        )

        # course enrollment for mock: upgrade deadline in the past
        self.enrollment_deadline_past = self.enrollment
        self.enrollment_deadline_past.course_upgrade_deadline = self.now - datetime.timedelta(days=1)
        self.enrollment_deadline_past.save()

        # course enrollment for mock: no upgrade deadline
        self.enrollment_deadline_missing = self.enrollment
        self.enrollment_deadline_missing.course_upgrade_deadline = None
        self.enrollment_deadline_missing.save()

    def test_tool_visible_logged_in(self):
        self.course_financial_mode.save()
        self.assertTrue(FinancialAssistanceTool().is_enabled(self.request, self.course.id))

    def test_tool_not_visible_when_not_eligible(self):
        self.course_overview.eligible_for_financial_aid = False
        self.course_overview.save()
        self.assertFalse(FinancialAssistanceTool().is_enabled(self.request, self.course_overview.id))

    def test_tool_not_visible_when_user_not_enrolled(self):
        self.course_financial_mode.save()
        self.request.user = None
        self.assertFalse(FinancialAssistanceTool().is_enabled(self.request, self.course.id))

    # mock the response from get_enrollment to use enrollment with course_upgrade_deadline in the past
    @patch('lms.djangoapps.courseware.course_tools.CourseEnrollment.get_enrollment')
    def test_not_visible_when_upgrade_deadline_has_passed(self, get_enrollment_mock):
        get_enrollment_mock.return_value = self.enrollment_deadline_past
        self.assertFalse(FinancialAssistanceTool().is_enabled(self.request, self.course.id))

    # mock the response from get_enrollment to use enrollment with no course_upgrade_deadline
    @patch('lms.djangoapps.courseware.course_tools.CourseEnrollment.get_enrollment')
    def test_not_visible_when_no_upgrade_deadline(self, get_enrollment_mock):
        get_enrollment_mock.return_value = self.enrollment_deadline_missing
        self.assertFalse(FinancialAssistanceTool().is_enabled(self.request, self.course.id))

    def test_tool_not_visible_when_end_date_passed(self):
        self.course_overview.end_date = self.now - datetime.timedelta(days=30)
        self.course_overview.save()
        self.assertFalse(FinancialAssistanceTool().is_enabled(self.request, self.course_overview.id))

    # mock the response from get_enrollment to use enrollment where learner upgraded
    @patch('lms.djangoapps.courseware.course_tools.CourseEnrollment.get_enrollment')
    def test_tool_not_visible_when_already_upgraded(self, get_enrollment_mock):
        self.course_financial_mode.save()
        get_enrollment_mock.return_value = self.enrollment_upgraded
        self.assertFalse(FinancialAssistanceTool().is_enabled(self.request, self.course.id))
