# -*- coding: utf-8 -*-
"""Tests for course home page date summary blocks."""
from datetime import datetime, timedelta

import ddt
from django.core.urlresolvers import reverse
from freezegun import freeze_time
from nose.plugins.attrib import attr
from pytz import utc

from commerce.models import CommerceConfiguration
from course_modes.tests.factories import CourseModeFactory
from course_modes.models import CourseMode
from courseware.courses import _get_course_date_summary_blocks
from courseware.date_summary import (
    CourseEndDate,
    CourseStartDate,
    DateSummary,
    TodaysDate,
    VerificationDeadlineDate,
    VerifiedUpgradeDeadlineDate,
)
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.verify_student.models import VerificationDeadline
from lms.djangoapps.verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr('shard_1')
@ddt.ddt
class CourseDateSummaryTest(SharedModuleStoreTestCase):
    """Tests for course date summary blocks."""

    def setUp(self):
        SelfPacedConfiguration(enable_course_home_improvements=True).save()
        super(CourseDateSummaryTest, self).setUp()

    def setup_course_and_user(
            self,
            days_till_start=1,
            days_till_end=14,
            days_till_upgrade_deadline=4,
            enroll_user=True,
            enrollment_mode=CourseMode.VERIFIED,
            course_min_price=100,
            days_till_verification_deadline=14,
            verification_status=None,
            sku=None
    ):
        """Set up the course and user for this test."""
        now = datetime.now(utc)
        self.course = CourseFactory.create(  # pylint: disable=attribute-defined-outside-init
            start=now + timedelta(days=days_till_start)
        )
        self.user = UserFactory.create()  # pylint: disable=attribute-defined-outside-init

        if days_till_end is not None:
            self.course.end = now + timedelta(days=days_till_end)
        else:
            self.course.end = None

        if enrollment_mode is not None and days_till_upgrade_deadline is not None:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=enrollment_mode,
                expiration_datetime=now + timedelta(days=days_till_upgrade_deadline),
                min_price=course_min_price,
                sku=sku
            )

        if enroll_user:
            enrollment_mode = enrollment_mode or CourseMode.DEFAULT_MODE_SLUG
            CourseEnrollmentFactory.create(course_id=self.course.id, user=self.user, mode=enrollment_mode)

        if days_till_verification_deadline is not None:
            VerificationDeadline.objects.create(
                course_key=self.course.id,
                deadline=now + timedelta(days=days_till_verification_deadline)
            )

        if verification_status is not None:
            SoftwareSecurePhotoVerificationFactory.create(user=self.user, status=verification_status)

    def test_course_info_feature_flag(self):
        SelfPacedConfiguration(enable_course_home_improvements=False).save()
        self.setup_course_and_user()
        url = reverse('info', args=(self.course.id,))
        response = self.client.get(url)
        self.assertNotIn('date-summary', response.content)

    # Tests for which blocks are enabled

    def assert_block_types(self, expected_blocks):
        """Assert that the enabled block types for this course are as expected."""
        blocks = _get_course_date_summary_blocks(self.course, self.user)
        self.assertEqual(len(blocks), len(expected_blocks))
        self.assertEqual(set(type(b) for b in blocks), set(expected_blocks))

    @ddt.data(
        # Verified enrollment with no photo-verification before course start
        ({}, (CourseEndDate, CourseStartDate, TodaysDate, VerificationDeadlineDate)),
        # Verified enrollment with `approved` photo-verification after course end
        ({'days_till_start': -10,
          'days_till_end': -5,
          'days_till_upgrade_deadline': -6,
          'days_till_verification_deadline': -5,
          'verification_status': 'approved'},
         (TodaysDate, CourseEndDate)),
        # Verified enrollment with `expired` photo-verification during course run
        ({'days_till_start': -10,
          'verification_status': 'expired'},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate)),
        # Verified enrollment with `approved` photo-verification during course run
        ({'days_till_start': -10,
          'verification_status': 'approved'},
         (TodaysDate, CourseEndDate)),
        # Audit enrollment and non-upsell course.
        ({'days_till_start': -10,
          'days_till_upgrade_deadline': None,
          'days_till_verification_deadline': None,
          'course_min_price': 0,
          'enrollment_mode': CourseMode.AUDIT},
         (TodaysDate, CourseEndDate)),
        # Verified enrollment with *NO* course end date
        ({'days_till_end': None},
         (CourseStartDate, TodaysDate, VerificationDeadlineDate)),
        # Verified enrollment with no photo-verification during course run
        ({'days_till_start': -1},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate)),
        # Verification approved
        ({'days_till_start': -10,
          'days_till_upgrade_deadline': -1,
          'days_till_verification_deadline': 1,
          'verification_status': 'approved'},
         (TodaysDate, CourseEndDate)),
        # After upgrade deadline
        ({'days_till_start': -10,
          'days_till_upgrade_deadline': -1},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate)),
        # After verification deadline
        ({'days_till_start': -10,
          'days_till_upgrade_deadline': -2,
          'days_till_verification_deadline': -1},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate)),
        # Un-enrolled user before course start
        ({'enroll_user': False},
         (CourseStartDate, TodaysDate, CourseEndDate, VerifiedUpgradeDeadlineDate)),
        # Un-enrolled user during course run
        ({'days_till_start': -1,
          'enroll_user': False},
         (TodaysDate, CourseEndDate, VerifiedUpgradeDeadlineDate)),
        # Un-enrolled user after course end.
        ({'enroll_user': False,
          'days_till_start': -10,
          'days_till_end': -5},
         (TodaysDate, CourseEndDate, VerifiedUpgradeDeadlineDate)),
    )
    @ddt.unpack
    def test_enabled_block_types(self, course_options, expected_blocks):
        self.setup_course_and_user(**course_options)
        self.assert_block_types(expected_blocks)

    # Specific block type tests

    ## Base DateSummary -- test empty defaults

    def test_date_summary(self):
        self.setup_course_and_user()
        block = DateSummary(self.course, self.user)
        html = '<div class="date-summary-container"><div class="date-summary date-summary-"></div></div>'
        self.assertHTMLEqual(block.render(), html)
        self.assertFalse(block.is_enabled)

    ## TodaysDate

    def _today_date_helper(self, expected_display_date):
        """
        Helper function to test that today's date block renders correctly
        and displays the correct time, accounting for daylight savings
        """
        self.setup_course_and_user()
        set_user_preference(self.user, "time_zone", "America/Los_Angeles")
        block = TodaysDate(self.course, self.user)
        self.assertTrue(block.is_enabled)
        self.assertEqual(block.date, datetime.now(utc))
        self.assertEqual(block.title, 'Today is {date}'.format(date=expected_display_date))
        self.assertNotIn('date-summary-date', block.render())

    @freeze_time('2015-11-01 08:59:00')
    def test_todays_date_time_zone_daylight(self):
        """
        Test today's date block displays correctly during
        daylight savings hours
        """
        self._today_date_helper('Nov 01, 2015 (01:59 PDT)')

    @freeze_time('2015-11-01 09:00:00')
    def test_todays_date_time_zone_normal(self):
        """
        Test today's date block displays correctly during
        normal daylight hours
        """
        self._today_date_helper('Nov 01, 2015 (01:00 PST)')

    @freeze_time('2015-01-02')
    def test_todays_date_render(self):
        self.setup_course_and_user()
        block = TodaysDate(self.course, self.user)
        self.assertIn('Jan 02, 2015', block.render())

    @freeze_time('2015-01-02')
    def test_todays_date_render_time_zone(self):
        self.setup_course_and_user()
        set_user_preference(self.user, "time_zone", "America/Los_Angeles")
        block = TodaysDate(self.course, self.user)
        # Today is 'Jan 01, 2015' because of time zone offset
        self.assertIn('Jan 01, 2015', block.render())

    ## CourseStartDate

    def test_course_start_date(self):
        self.setup_course_and_user()
        block = CourseStartDate(self.course, self.user)
        self.assertEqual(block.date, self.course.start)

    @freeze_time('2015-01-02')
    def test_start_date_render(self):
        self.setup_course_and_user()
        block = CourseStartDate(self.course, self.user)
        self.assertIn('in 1 day - Jan 03, 2015', block.render())

    @freeze_time('2015-01-02')
    def test_start_date_render_time_zone(self):
        self.setup_course_and_user()
        set_user_preference(self.user, "time_zone", "America/Los_Angeles")
        block = CourseStartDate(self.course, self.user)
        # Jan 02 is in 1 day because of time zone offset
        self.assertIn('in 1 day - Jan 02, 2015', block.render())

    ## CourseEndDate

    def test_course_end_date_for_certificate_eligible_mode(self):
        self.setup_course_and_user(days_till_start=-1)
        block = CourseEndDate(self.course, self.user)
        self.assertEqual(
            block.description,
            'To earn a certificate, you must complete all requirements before this date.'
        )

    def test_course_end_date_for_non_certificate_eligible_mode(self):
        self.setup_course_and_user(days_till_start=-1, enrollment_mode=CourseMode.AUDIT)
        block = CourseEndDate(self.course, self.user)
        self.assertEqual(
            block.description,
            'After this date, course content will be archived.'
        )

    def test_course_end_date_after_course(self):
        self.setup_course_and_user(days_till_start=-2, days_till_end=-1)
        block = CourseEndDate(self.course, self.user)
        self.assertEqual(
            block.description,
            'This course is archived, which means you can review course content but it is no longer active.'
        )

    ## VerifiedUpgradeDeadlineDate

    @freeze_time('2015-01-02')
    def test_verified_upgrade_deadline_date(self):
        self.setup_course_and_user(days_till_upgrade_deadline=1)
        block = VerifiedUpgradeDeadlineDate(self.course, self.user)
        self.assertEqual(block.date, datetime.now(utc) + timedelta(days=1))
        self.assertEqual(block.link, reverse('verify_student_upgrade_and_verify', args=(self.course.id,)))

    def test_without_upgrade_deadline(self):
        self.setup_course_and_user(enrollment_mode=None)
        block = VerifiedUpgradeDeadlineDate(self.course, self.user)
        self.assertIsNone(block.date)

    def test_ecommerce_checkout_redirect(self):
        """Verify the block link redirects to ecommerce checkout if it's enabled."""
        sku = 'TESTSKU'
        checkout_page = '/test_basket/'
        CommerceConfiguration.objects.create(
            checkout_on_ecommerce_service=True,
            single_course_checkout_page=checkout_page
        )
        self.setup_course_and_user(sku=sku)
        block = VerifiedUpgradeDeadlineDate(self.course, self.user)
        self.assertEqual(block.link, '{}?sku={}'.format(checkout_page, sku))

    ## VerificationDeadlineDate

    def test_no_verification_deadline(self):
        self.setup_course_and_user(days_till_start=-1, days_till_verification_deadline=None)
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertFalse(block.is_enabled)

    def test_no_verified_enrollment(self):
        self.setup_course_and_user(days_till_start=-1, enrollment_mode=CourseMode.AUDIT)
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertFalse(block.is_enabled)

    @freeze_time('2015-01-02')
    def test_verification_deadline_date_upcoming(self):
        self.setup_course_and_user(days_till_start=-1)
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertEqual(block.css_class, 'verification-deadline-upcoming')
        self.assertEqual(block.title, 'Verification Deadline')
        self.assertEqual(block.date, datetime.now(utc) + timedelta(days=14))
        self.assertEqual(
            block.description,
            'You must successfully complete verification before this date to qualify for a Verified Certificate.'
        )
        self.assertEqual(block.link_text, 'Verify My Identity')
        self.assertEqual(block.link, reverse('verify_student_verify_now', args=(self.course.id,)))

    @freeze_time('2015-01-02')
    def test_verification_deadline_date_retry(self):
        self.setup_course_and_user(days_till_start=-1, verification_status='denied')
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertEqual(block.css_class, 'verification-deadline-retry')
        self.assertEqual(block.title, 'Verification Deadline')
        self.assertEqual(block.date, datetime.now(utc) + timedelta(days=14))
        self.assertEqual(
            block.description,
            'You must successfully complete verification before this date to qualify for a Verified Certificate.'
        )
        self.assertEqual(block.link_text, 'Retry Verification')
        self.assertEqual(block.link, reverse('verify_student_reverify'))

    @freeze_time('2015-01-02')
    def test_verification_deadline_date_denied(self):
        self.setup_course_and_user(
            days_till_start=-10,
            verification_status='denied',
            days_till_verification_deadline=-1,
        )
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertEqual(block.css_class, 'verification-deadline-passed')
        self.assertEqual(block.title, 'Missed Verification Deadline')
        self.assertEqual(block.date, datetime.now(utc) + timedelta(days=-1))
        self.assertEqual(
            block.description,
            "Unfortunately you missed this course's deadline for a successful verification."
        )
        self.assertEqual(block.link_text, 'Learn More')
        self.assertEqual(block.link, '')

    @freeze_time('2015-01-02')
    @ddt.data(
        (-1, '1 day ago - Jan 01, 2015'),
        (1, 'in 1 day - Jan 03, 2015')
    )
    @ddt.unpack
    def test_render_date_string_past(self, delta, expected_date_string):
        self.setup_course_and_user(
            days_till_start=-10,
            verification_status='denied',
            days_till_verification_deadline=delta,
        )
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertEqual(block.get_context()['date'], expected_date_string)

    @freeze_time('2015-01-02')
    @ddt.data(
        # dates reflected from Jan 01, 2015 because of time zone offset
        (-1, '1 day ago - Dec 31, 2014'),
        (1, 'in 1 day - Jan 02, 2015')
    )
    @ddt.unpack
    def test_render_date_string_time_zone(self, delta, expected_date_string):
        self.setup_course_and_user(
            days_till_start=-10,
            verification_status='denied',
            days_till_verification_deadline=delta,
        )
        set_user_preference(self.user, "time_zone", "America/Los_Angeles")
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertEqual(block.get_context()['date'], expected_date_string)
