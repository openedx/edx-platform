# -*- coding: utf-8 -*-
"""Tests for course home page date summary blocks."""
from datetime import datetime, timedelta

import ddt
import waffle
from django.contrib.messages.middleware import MessageMiddleware
from django.urls import reverse
from django.test import RequestFactory
from freezegun import freeze_time
from mock import patch
from pytz import utc

from openedx.core.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.course_modes.tests.factories import CourseModeFactory
from courseware.courses import get_course_date_blocks
from courseware.date_summary import (
    CertificateAvailableDate,
    CourseEndDate,
    CourseStartDate,
    TodaysDate,
    VerificationDeadlineDate,
    VerifiedUpgradeDeadlineDate
)
from courseware.models import (
    CourseDynamicUpgradeDeadlineConfiguration,
    DynamicUpgradeDeadlineConfiguration,
    OrgDynamicUpgradeDeadlineConfiguration
)
from lms.djangoapps.commerce.models import CommerceConfiguration
from lms.djangoapps.verify_student.models import VerificationDeadline
from lms.djangoapps.verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.schedules.signals import CREATE_SCHEDULE_WAFFLE_FLAG
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.features.course_experience import UNIFIED_COURSE_TAB_FLAG, UPGRADE_DEADLINE_MESSAGE, CourseHomeMessages
from student.tests.factories import TEST_PASSWORD, CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class CourseDateSummaryTest(SharedModuleStoreTestCase):
    """Tests for course date summary blocks."""

    def setUp(self):
        super(CourseDateSummaryTest, self).setUp()
        SelfPacedConfiguration.objects.create(enable_course_home_improvements=True)

    def test_course_info_feature_flag(self):
        SelfPacedConfiguration(enable_course_home_improvements=False).save()
        course = create_course_run()
        user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)

        self.client.login(username=user.username, password=TEST_PASSWORD)
        url = reverse('info', args=(course.id,))
        response = self.client.get(url)
        self.assertNotIn('date-summary', response.content)

    def test_course_home_logged_out(self):
        course = create_course_run()
        url = reverse('openedx.course_experience.course_home', args=(course.id,))
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    # Tests for which blocks are enabled
    def assert_block_types(self, course, user, expected_blocks):
        """Assert that the enabled block types for this course are as expected."""
        blocks = get_course_date_blocks(course, user)
        self.assertEqual(len(blocks), len(expected_blocks))
        self.assertEqual(set(type(b) for b in blocks), set(expected_blocks))

    @ddt.data(
        # Verified enrollment with no photo-verification before course start
        ({}, {}, (CourseEndDate, CourseStartDate, TodaysDate, VerificationDeadlineDate)),
        # Verified enrollment with `approved` photo-verification after course end
        ({'days_till_start': -10,
          'days_till_end': -5,
          'days_till_upgrade_deadline': -6,
          'days_till_verification_deadline': -5,
          },
         {'verification_status': 'approved'},
         (TodaysDate, CourseEndDate)),
        # Verified enrollment with `expired` photo-verification during course run
        ({'days_till_start': -10},
         {'verification_status': 'expired'},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate)),
        # Verified enrollment with `approved` photo-verification during course run
        ({'days_till_start': -10, },
         {'verification_status': 'approved'},
         (TodaysDate, CourseEndDate)),
        # Verified enrollment with *NO* course end date
        ({'days_till_end': None},
         {},
         (CourseStartDate, TodaysDate, VerificationDeadlineDate)),
        # Verified enrollment with no photo-verification during course run
        ({'days_till_start': -1},
         {},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate)),
        # Verification approved
        ({'days_till_start': -10,
          'days_till_upgrade_deadline': -1,
          'days_till_verification_deadline': 1,
          },
         {'verification_status': 'approved'},
         (TodaysDate, CourseEndDate)),
        # After upgrade deadline
        ({'days_till_start': -10,
          'days_till_upgrade_deadline': -1},
         {},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate)),
        # After verification deadline
        ({'days_till_start': -10,
          'days_till_upgrade_deadline': -2,
          'days_till_verification_deadline': -1},
         {},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate)),
    )
    @ddt.unpack
    def test_enabled_block_types(self, course_kwargs, user_kwargs, expected_blocks):
        course = create_course_run(**course_kwargs)
        user = create_user(**user_kwargs)
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)
        self.assert_block_types(course, user, expected_blocks)

    @ddt.data(
        # Course not started
        ({}, (CourseStartDate, TodaysDate, CourseEndDate)),
        # Course active
        ({'days_till_start': -1}, (TodaysDate, CourseEndDate)),
        # Course ended
        ({'days_till_start': -10, 'days_till_end': -5},
         (TodaysDate, CourseEndDate)),
    )
    @ddt.unpack
    def test_enabled_block_types_without_enrollment(self, course_kwargs, expected_blocks):
        course = create_course_run(**course_kwargs)
        user = create_user()
        self.assert_block_types(course, user, expected_blocks)

    def test_enabled_block_types_with_non_upgradeable_course_run(self):
        course = create_course_run(days_till_start=-10, days_till_verification_deadline=None)
        user = create_user()
        CourseMode.objects.get(course_id=course.id, mode_slug=CourseMode.VERIFIED).delete()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.AUDIT)
        self.assert_block_types(course, user, (TodaysDate, CourseEndDate))

    def test_todays_date_block(self):
        """
        Helper function to test that today's date block renders correctly
        and displays the correct time, accounting for daylight savings
        """
        with freeze_time('2015-01-02'):
            course = create_course_run()
            user = create_user()
            block = TodaysDate(course, user)
            self.assertTrue(block.is_enabled)
            self.assertEqual(block.date, datetime.now(utc))
            self.assertEqual(block.title, 'current_datetime')

    @ddt.data(
        'info',
        'openedx.course_experience.course_home',
    )
    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
    def test_todays_date_no_timezone(self, url_name):
        with freeze_time('2015-01-02'):
            course = create_course_run()
            user = create_user()
            self.client.login(username=user.username, password=TEST_PASSWORD)

            html_elements = [
                '<h3 class="hd hd-6 handouts-header">Important Course Dates</h3>',
                '<div class="date-summary-container">',
                '<div class="date-summary date-summary-todays-date">',
                '<span class="hd hd-6 heading localized-datetime"',
                'data-datetime="2015-01-02 00:00:00+00:00"',
                u'data-string="Today is {date}"',
                'data-timezone="None"'
            ]
            url = reverse(url_name, args=(course.id,))
            response = self.client.get(url, follow=True)
            for html in html_elements:
                self.assertContains(response, html)

    @ddt.data(
        'info',
        'openedx.course_experience.course_home',
    )
    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
    def test_todays_date_timezone(self, url_name):
        with freeze_time('2015-01-02'):
            course = create_course_run()
            user = create_user()
            self.client.login(username=user.username, password=TEST_PASSWORD)
            set_user_preference(user, 'time_zone', 'America/Los_Angeles')
            url = reverse(url_name, args=(course.id,))
            response = self.client.get(url, follow=True)

            html_elements = [
                '<h3 class="hd hd-6 handouts-header">Important Course Dates</h3>',
                '<div class="date-summary-container">',
                '<div class="date-summary date-summary-todays-date">',
                '<span class="hd hd-6 heading localized-datetime"',
                'data-datetime="2015-01-02 00:00:00+00:00"',
                u'data-string="Today is {date}"',
                'data-timezone="America/Los_Angeles"'
            ]
            for html in html_elements:
                self.assertContains(response, html)

    ## Tests Course Start Date
    def test_course_start_date(self):
        course = create_course_run()
        user = create_user()
        block = CourseStartDate(course, user)
        self.assertEqual(block.date, course.start)

    @ddt.data(
        'info',
        'openedx.course_experience.course_home',
    )
    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
    def test_start_date_render(self, url_name):
        with freeze_time('2015-01-02'):
            course = create_course_run()
            user = create_user()
            self.client.login(username=user.username, password=TEST_PASSWORD)
            url = reverse(url_name, args=(course.id,))
            response = self.client.get(url, follow=True)
            html_elements = [
                u'data-string="in 1 day - {date}"',
                'data-datetime="2015-01-03 00:00:00+00:00"'
            ]
            for html in html_elements:
                self.assertContains(response, html)

    @ddt.data(
        'info',
        'openedx.course_experience.course_home',
    )
    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
    def test_start_date_render_time_zone(self, url_name):
        with freeze_time('2015-01-02'):
            course = create_course_run()
            user = create_user()
            self.client.login(username=user.username, password=TEST_PASSWORD)
            set_user_preference(user, 'time_zone', 'America/Los_Angeles')
            url = reverse(url_name, args=(course.id,))
            response = self.client.get(url, follow=True)
            html_elements = [
                u'data-string="in 1 day - {date}"',
                'data-datetime="2015-01-03 00:00:00+00:00"',
                'data-timezone="America/Los_Angeles"'
            ]
            for html in html_elements:
                self.assertContains(response, html)

    ## Tests Course End Date Block
    def test_course_end_date_for_certificate_eligible_mode(self):
        course = create_course_run(days_till_start=-1)
        user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)
        block = CourseEndDate(course, user)
        self.assertEqual(
            block.description,
            'To earn a certificate, you must complete all requirements before this date.'
        )

    def test_course_end_date_for_non_certificate_eligible_mode(self):
        course = create_course_run(days_till_start=-1)
        user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.AUDIT)
        block = CourseEndDate(course, user)
        self.assertEqual(
            block.description,
            'After this date, course content will be archived.'
        )
        self.assertEqual(block.title, 'Course End')

    def test_course_end_date_after_course(self):
        course = create_course_run(days_till_start=-2, days_till_end=-1)
        user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)
        block = CourseEndDate(course, user)
        self.assertEqual(
            block.description,
            'This course is archived, which means you can review course content but it is no longer active.'
        )
        self.assertEqual(block.title, 'Course End')

    def test_ecommerce_checkout_redirect(self):
        """Verify the block link redirects to ecommerce checkout if it's enabled."""
        sku = 'TESTSKU'
        configuration = CommerceConfiguration.objects.create(checkout_on_ecommerce_service=True)
        course = create_course_run()
        user = create_user()
        course_mode = CourseMode.objects.get(course_id=course.id, mode_slug=CourseMode.VERIFIED)
        course_mode.sku = sku
        course_mode.save()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)

        block = VerifiedUpgradeDeadlineDate(course, user)
        self.assertEqual(block.link, '{}?sku={}'.format(configuration.basket_checkout_page, sku))

    ## CertificateAvailableDate
    @waffle.testutils.override_switch('certificates.auto_certificate_generation', True)
    def test_no_certificate_available_date(self):
        course = create_course_run(days_till_start=-1)
        user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.AUDIT)
        block = CertificateAvailableDate(course, user)
        self.assertEqual(block.date, None)
        self.assertFalse(block.is_enabled)

    ## CertificateAvailableDate
    @waffle.testutils.override_switch('certificates.auto_certificate_generation', True)
    def test_no_certificate_available_date_for_self_paced(self):
        course = create_self_paced_course_run()
        verified_user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=verified_user, mode=CourseMode.VERIFIED)
        course.certificate_available_date = datetime.now(utc) + timedelta(days=7)
        course.save()
        block = CertificateAvailableDate(course, verified_user)
        self.assertNotEqual(block.date, None)
        self.assertFalse(block.is_enabled)

    def test_no_certificate_available_date_for_audit_course(self):
        """
        Tests that Certificate Available Date is not visible in the course "Important Course Dates" section
        if the course only has audit mode.
        """
        course = create_course_run()
        audit_user = create_user()

        # Enroll learner in the audit mode and verify the course only has 1 mode (audit)
        CourseEnrollmentFactory(course_id=course.id, user=audit_user, mode=CourseMode.AUDIT)
        CourseMode.objects.get(course_id=course.id, mode_slug=CourseMode.VERIFIED).delete()
        all_course_modes = CourseMode.modes_for_course(course.id)
        self.assertEqual(len(all_course_modes), 1)
        self.assertEqual(all_course_modes[0].slug, CourseMode.AUDIT)

        course.certificate_available_date = datetime.now(utc) + timedelta(days=7)
        course.save()

        # Verify Certificate Available Date is not enabled for learner.
        block = CertificateAvailableDate(course, audit_user)
        self.assertFalse(block.is_enabled)
        self.assertNotEqual(block.date, None)

    @waffle.testutils.override_switch('certificates.auto_certificate_generation', True)
    def test_certificate_available_date_defined(self):
        course = create_course_run()
        audit_user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=audit_user, mode=CourseMode.AUDIT)
        verified_user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=verified_user, mode=CourseMode.VERIFIED)
        course.certificate_available_date = datetime.now(utc) + timedelta(days=7)
        enable_course_certificates(course)
        CertificateAvailableDate(course, audit_user)
        for block in (CertificateAvailableDate(course, audit_user), CertificateAvailableDate(course, verified_user)):
            self.assertIsNotNone(course.certificate_available_date)
            self.assertEqual(block.date, course.certificate_available_date)
            self.assertTrue(block.is_enabled)

    ## VerificationDeadlineDate
    def test_no_verification_deadline(self):
        course = create_course_run(days_till_start=-1, days_till_verification_deadline=None)
        user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)
        block = VerificationDeadlineDate(course, user)
        self.assertFalse(block.is_enabled)

    def test_no_verified_enrollment(self):
        course = create_course_run(days_till_start=-1)
        user = create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.AUDIT)
        block = VerificationDeadlineDate(course, user)
        self.assertFalse(block.is_enabled)

    def test_verification_deadline_date_upcoming(self):
        with freeze_time('2015-01-02'):
            course = create_course_run(days_till_start=-1)
            user = create_user()
            CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)

            block = VerificationDeadlineDate(course, user)
            self.assertEqual(block.css_class, 'verification-deadline-upcoming')
            self.assertEqual(block.title, 'Verification Deadline')
            self.assertEqual(block.date, datetime.now(utc) + timedelta(days=14))
            self.assertEqual(
                block.description,
                'You must successfully complete verification before this date to qualify for a Verified Certificate.'
            )
            self.assertEqual(block.link_text, 'Verify My Identity')
            self.assertEqual(block.link, reverse('verify_student_verify_now', args=(course.id,)))

    def test_verification_deadline_date_retry(self):
        with freeze_time('2015-01-02'):
            course = create_course_run(days_till_start=-1)
            user = create_user(verification_status='denied')
            CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)

            block = VerificationDeadlineDate(course, user)
            self.assertEqual(block.css_class, 'verification-deadline-retry')
            self.assertEqual(block.title, 'Verification Deadline')
            self.assertEqual(block.date, datetime.now(utc) + timedelta(days=14))
            self.assertEqual(
                block.description,
                'You must successfully complete verification before this date to qualify for a Verified Certificate.'
            )
            self.assertEqual(block.link_text, 'Retry Verification')
            self.assertEqual(block.link, reverse('verify_student_reverify'))

    def test_verification_deadline_date_denied(self):
        with freeze_time('2015-01-02'):
            course = create_course_run(days_till_start=-10, days_till_verification_deadline=-1)
            user = create_user(verification_status='denied')
            CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)

            block = VerificationDeadlineDate(course, user)
            self.assertEqual(block.css_class, 'verification-deadline-passed')
            self.assertEqual(block.title, 'Missed Verification Deadline')
            self.assertEqual(block.date, datetime.now(utc) + timedelta(days=-1))
            self.assertEqual(
                block.description,
                "Unfortunately you missed this course's deadline for a successful verification."
            )
            self.assertEqual(block.link_text, 'Learn More')
            self.assertEqual(block.link, '')

    @ddt.data(
        (-1, u'1 day ago - {date}'),
        (1, u'in 1 day - {date}')
    )
    @ddt.unpack
    def test_render_date_string_past(self, delta, expected_date_string):
        with freeze_time('2015-01-02'):
            course = create_course_run(days_till_start=-10, days_till_verification_deadline=delta)
            user = create_user(verification_status='denied')
            CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)

            block = VerificationDeadlineDate(course, user)
            self.assertEqual(block.relative_datestring, expected_date_string)


@ddt.ddt
class TestDateAlerts(SharedModuleStoreTestCase):
    """
    Unit tests for date alerts.
    """
    def setUp(self):
        super(TestDateAlerts, self).setUp()
        with freeze_time('2017-07-01 09:00:00'):
            self.course = create_course_run(days_till_start=0)
            self.course.certificate_available_date = self.course.start + timedelta(days=21)
            enable_course_certificates(self.course)
            self.enrollment = CourseEnrollmentFactory(course_id=self.course.id, mode=CourseMode.AUDIT)
            self.request = RequestFactory().request()
            self.request.session = {}
            self.request.user = self.enrollment.user
            MessageMiddleware().process_request(self.request)

    @ddt.data(
        ['2017-01-01 09:00:00', u'in 6 months on <span class="date localized-datetime" data-format="shortDate"'],
        ['2017-06-17 09:00:00', u'in 2 weeks on <span class="date localized-datetime" data-format="shortDate"'],
        ['2017-06-30 10:00:00', u'in 1 day at <span class="date localized-datetime" data-format="shortTime"'],
        ['2017-07-01 08:00:00', u'in 1 hour at <span class="date localized-datetime" data-format="shortTime"'],
        ['2017-07-01 08:55:00', u'in 5 minutes at <span class="date localized-datetime" data-format="shortTime"'],
        ['2017-07-01 09:00:00', None],
        ['2017-08-01 09:00:00', None],
    )
    @ddt.unpack
    def test_start_date_alert(self, current_time, expected_message_html):
        """
        Verify that course start date alerts are registered.
        """
        with freeze_time(current_time):
            block = CourseStartDate(self.course, self.request.user)
            block.register_alerts(self.request, self.course)
            messages = list(CourseHomeMessages.user_messages(self.request))
            if expected_message_html:
                self.assertEqual(len(messages), 1)
                self.assertIn(expected_message_html, messages[0].message_html)
            else:
                self.assertEqual(len(messages), 0)

    @ddt.data(
        ['2017-06-30 09:00:00', None],
        ['2017-07-01 09:00:00', u'in 2 weeks on <span class="date localized-datetime" data-format="shortDate"'],
        ['2017-07-14 10:00:00', u'in 1 day at <span class="date localized-datetime" data-format="shortTime"'],
        ['2017-07-15 08:00:00', u'in 1 hour at <span class="date localized-datetime" data-format="shortTime"'],
        ['2017-07-15 08:55:00', u'in 5 minutes at <span class="date localized-datetime" data-format="shortTime"'],
        ['2017-07-15 09:00:00', None],
        ['2017-08-15 09:00:00', None],
    )
    @ddt.unpack
    def test_end_date_alert(self, current_time, expected_message_html):
        """
        Verify that course end date alerts are registered.
        """
        with freeze_time(current_time):
            block = CourseEndDate(self.course, self.request.user)
            block.register_alerts(self.request, self.course)
            messages = list(CourseHomeMessages.user_messages(self.request))
            if expected_message_html:
                self.assertEqual(len(messages), 1)
                self.assertIn(expected_message_html, messages[0].message_html)
            else:
                self.assertEqual(len(messages), 0)

    @ddt.data(
        ['2017-06-20 09:00:00', None],
        ['2017-06-21 09:00:00', u'Don&#39;t forget, you have 2 weeks left to upgrade to a Verified Certificate.'],
        ['2017-07-04 10:00:00', u'Don&#39;t forget, you have 1 day left to upgrade to a Verified Certificate.'],
        ['2017-07-05 08:00:00', u'Don&#39;t forget, you have 1 hour left to upgrade to a Verified Certificate.'],
        ['2017-07-05 08:55:00', u'Don&#39;t forget, you have 5 minutes left to upgrade to a Verified Certificate.'],
        ['2017-07-05 09:00:00', None],
        ['2017-08-05 09:00:00', None],
    )
    @ddt.unpack
    @override_waffle_flag(UPGRADE_DEADLINE_MESSAGE, active=True)
    def test_verified_upgrade_deadline_alert(self, current_time, expected_message_html):
        """
        Verify the verified upgrade deadline alerts.
        """
        with freeze_time(current_time):
            block = VerifiedUpgradeDeadlineDate(self.course, self.request.user)
            block.register_alerts(self.request, self.course)
            messages = list(CourseHomeMessages.user_messages(self.request))
            if expected_message_html:
                self.assertEqual(len(messages), 1)
                self.assertIn(expected_message_html, messages[0].message_html)
            else:
                self.assertEqual(len(messages), 0)

    @ddt.data(
        ['2017-07-15 08:00:00', None],
        ['2017-07-15 09:00:00', u'If you have earned a certificate, you will be able to access it 1 week from now.'],
        ['2017-07-21 09:00:00', u'If you have earned a certificate, you will be able to access it 1 day from now.'],
        ['2017-07-22 08:00:00', u'If you have earned a certificate, you will be able to access it 1 hour from now.'],
        ['2017-07-22 09:00:00', None],
        ['2017-07-23 09:00:00', None],
    )
    @ddt.unpack
    @waffle.testutils.override_switch('certificates.auto_certificate_generation', True)
    def test_certificate_availability_alert(self, current_time, expected_message_html):
        """
        Verify the verified upgrade deadline alerts.
        """
        with freeze_time(current_time):
            block = CertificateAvailableDate(self.course, self.request.user)
            block.register_alerts(self.request, self.course)
            messages = list(CourseHomeMessages.user_messages(self.request))
            if expected_message_html:
                self.assertEqual(len(messages), 1)
                self.assertIn(expected_message_html, messages[0].message_html)
            else:
                self.assertEqual(len(messages), 0)


@ddt.ddt
class TestScheduleOverrides(SharedModuleStoreTestCase):

    def setUp(self):
        super(TestScheduleOverrides, self).setUp()

        patcher = patch('openedx.core.djangoapps.schedules.signals.get_current_site')
        mock_get_current_site = patcher.start()
        self.addCleanup(patcher.stop)

        mock_get_current_site.return_value = SiteFactory.create()

    @override_waffle_flag(CREATE_SCHEDULE_WAFFLE_FLAG, True)
    def test_date_with_self_paced_with_enrollment_before_course_start(self):
        """ Enrolling before a course begins should result in the upgrade deadline being set relative to the
        course start date. """
        global_config = DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        course = create_self_paced_course_run(days_till_start=3)
        overview = CourseOverview.get_from_id(course.id)
        expected = overview.start + timedelta(days=global_config.deadline_days)
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        self.assertEqual(block.date, expected)
        self._check_text(block)

    def _check_text(self, upgrade_date_summary):
        self.assertEqual(upgrade_date_summary.title, 'Upgrade to Verified Certificate')
        self.assertEqual(
            upgrade_date_summary.description,
            'Don\'t miss the opportunity to highlight your new knowledge and skills by earning a verified'
            ' certificate.'
        )
        self.assertEqual(upgrade_date_summary.relative_datestring, u'by {date}')

    @override_waffle_flag(CREATE_SCHEDULE_WAFFLE_FLAG, True)
    def test_date_with_self_paced_with_enrollment_after_course_start(self):
        """ Enrolling after a course begins should result in the upgrade deadline being set relative to the
        enrollment date.

        Additionally, OrgDynamicUpgradeDeadlineConfiguration should override the number of days until the deadline,
        and CourseDynamicUpgradeDeadlineConfiguration should override the org-level override.
        """
        global_config = DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        course = create_self_paced_course_run(days_till_start=-1, org_id='TestOrg')
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        expected = enrollment.created + timedelta(days=global_config.deadline_days)
        self.assertEqual(block.date, expected)

        # Orgs should be able to override the deadline
        org_config = OrgDynamicUpgradeDeadlineConfiguration.objects.create(
            enabled=True, org_id=course.org, deadline_days=4
        )
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        expected = enrollment.created + timedelta(days=org_config.deadline_days)
        self.assertEqual(block.date, expected)

        # Courses should be able to override the deadline (and the org-level override)
        course_config = CourseDynamicUpgradeDeadlineConfiguration.objects.create(
            enabled=True, course_id=course.id, deadline_days=3
        )
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        expected = enrollment.created + timedelta(days=course_config.deadline_days)
        self.assertEqual(block.date, expected)

    @override_waffle_flag(CREATE_SCHEDULE_WAFFLE_FLAG, True)
    def test_date_with_self_paced_without_dynamic_upgrade_deadline(self):
        """ Disabling the dynamic upgrade deadline functionality should result in the verified mode's
        expiration date being returned. """
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=False)
        course = create_self_paced_course_run()
        expected = CourseMode.objects.get(course_id=course.id, mode_slug=CourseMode.VERIFIED).expiration_datetime
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        self.assertEqual(block.date, expected)

    @override_waffle_flag(CREATE_SCHEDULE_WAFFLE_FLAG, True)
    def test_date_with_existing_schedule(self):
        """ If a schedule is created while deadlines are disabled, they shouldn't magically appear once the feature is
        turned on. """
        course = create_self_paced_course_run(days_till_start=-1)
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=False)
        course_config = CourseDynamicUpgradeDeadlineConfiguration.objects.create(enabled=False, course_id=course.id)
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)

        # The enrollment has a schedule, but the upgrade deadline should be None
        self.assertIsNone(enrollment.schedule.upgrade_deadline)

        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        expected = CourseMode.objects.get(course_id=course.id, mode_slug=CourseMode.VERIFIED).expiration_datetime
        self.assertEqual(block.date, expected)

        # Now if we turn on the feature for this course, this existing enrollment should be unaffected
        course_config.enabled = True
        course_config.save()

        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        self.assertEqual(block.date, expected)

    @ddt.data(
        # (enroll before configs, org enabled, org opt-out, course enabled, course opt-out, expected dynamic deadline)
        (False, False, False, False, False, True),
        (False, False, False, False, True, True),
        (False, False, False, True, False, True),
        (False, False, False, True, True, False),
        (False, False, True, False, False, True),
        (False, False, True, False, True, True),
        (False, False, True, True, False, True),
        (False, False, True, True, True, False),
        (False, True, False, False, False, True),
        (False, True, False, False, True, True),
        (False, True, False, True, False, True),
        (False, True, False, True, True, False),  # course-level overrides org-level
        (False, True, True, False, False, False),
        (False, True, True, False, True, False),
        (False, True, True, True, False, True),  # course-level overrides org-level
        (False, True, True, True, True, False),

        (True, False, False, False, False, True),
        (True, False, False, False, True, True),
        (True, False, False, True, False, True),
        (True, False, False, True, True, False),
        (True, False, True, False, False, True),
        (True, False, True, False, True, True),
        (True, False, True, True, False, True),
        (True, False, True, True, True, False),
        (True, True, False, False, False, True),
        (True, True, False, False, True, True),
        (True, True, False, True, False, True),
        (True, True, False, True, True, False),  # course-level overrides org-level
        (True, True, True, False, False, False),
        (True, True, True, False, True, False),
        (True, True, True, True, False, True),  # course-level overrides org-level
        (True, True, True, True, True, False),
    )
    @ddt.unpack
    @override_waffle_flag(CREATE_SCHEDULE_WAFFLE_FLAG, True)
    def test_date_with_org_and_course_config_overrides(self, enroll_first, org_config_enabled, org_config_opt_out,
                                                       course_config_enabled, course_config_opt_out,
                                                       expected_dynamic_deadline):
        """ Runs through every combination of org-level plus course-level DynamicUpgradeDeadlineConfiguration enabled
        and opt-out states to verify that course-level overrides the org-level config. """
        course = create_self_paced_course_run(days_till_start=-1, org_id='TestOrg')
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        if enroll_first:
            enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT, course__self_paced=True)
        OrgDynamicUpgradeDeadlineConfiguration.objects.create(
            enabled=org_config_enabled, opt_out=org_config_opt_out, org_id=course.id.org
        )
        CourseDynamicUpgradeDeadlineConfiguration.objects.create(
            enabled=course_config_enabled, opt_out=course_config_opt_out, course_id=course.id
        )
        if not enroll_first:
            enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT, course__self_paced=True)

        # The enrollment has a schedule, and the upgrade_deadline is set when expected_dynamic_deadline is True
        if not enroll_first:
            self.assertEqual(enrollment.schedule.upgrade_deadline is not None, expected_dynamic_deadline)
        # The CourseEnrollment.upgrade_deadline property method is checking the configs
        self.assertEqual(enrollment.dynamic_upgrade_deadline is not None, expected_dynamic_deadline)


def create_user(verification_status=None):
    """ Create a new User instance.

    Arguments:
        verification_status (str): User's verification status. If this value is set an instance of
            SoftwareSecurePhotoVerification will be created for the user with the specified status.
    """
    user = UserFactory()

    if verification_status is not None:
        SoftwareSecurePhotoVerificationFactory.create(user=user, status=verification_status)

    return user


def create_course_run(
    days_till_start=1, days_till_end=14, days_till_upgrade_deadline=4, days_till_verification_deadline=14,
):
    """ Create a new course run and course modes.

    All date-related arguments are relative to the current date-time (now) unless otherwise specified.

    Both audit and verified `CourseMode` objects will be created for the course run.

    Arguments:
        days_till_end (int): Number of days until the course ends.
        days_till_start (int): Number of days until the course starts.
        days_till_upgrade_deadline (int): Number of days until the course run's upgrade deadline.
        days_till_verification_deadline (int): Number of days until the course run's verification deadline. If this
            value is set to `None` no deadline will be verification deadline will be created.
    """
    now = datetime.now(utc)
    course = CourseFactory.create(start=now + timedelta(days=days_till_start))

    course.end = None
    if days_till_end is not None:
        course.end = now + timedelta(days=days_till_end)

    CourseModeFactory(course_id=course.id, mode_slug=CourseMode.AUDIT)
    CourseModeFactory(
        course_id=course.id,
        mode_slug=CourseMode.VERIFIED,
        expiration_datetime=now + timedelta(days=days_till_upgrade_deadline)
    )

    if days_till_verification_deadline is not None:
        VerificationDeadline.objects.create(
            course_key=course.id,
            deadline=now + timedelta(days=days_till_verification_deadline)
        )

    return course


def create_self_paced_course_run(days_till_start=1, org_id=None):
    """ Create a new course run and course modes.

    All date-related arguments are relative to the current date-time (now) unless otherwise specified.

    Both audit and verified `CourseMode` objects will be created for the course run.

    Arguments:
        days_till_start (int): Number of days until the course starts.
        org_id (string): String org id to assign the course to (default: None; use CourseFactory default)
    """
    now = datetime.now(utc)
    course = CourseFactory.create(start=now + timedelta(days=days_till_start), self_paced=True,
                                  org=org_id if org_id else 'TestedX')

    CourseModeFactory(
        course_id=course.id,
        mode_slug=CourseMode.AUDIT
    )
    CourseModeFactory(
        course_id=course.id,
        mode_slug=CourseMode.VERIFIED,
        expiration_datetime=now + timedelta(days=100)
    )

    return course


def enable_course_certificates(course):
    """
    Enable course certificate configuration.
    """
    course.certificates = {
        u'certificates': [{
            u'course_title': u'Test',
            u'name': u'',
            u'is_active': True,
        }]
    }
    course.save()
