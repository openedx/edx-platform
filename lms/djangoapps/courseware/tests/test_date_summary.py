# -*- coding: utf-8 -*-
"""Tests for course home page date summary blocks."""
from datetime import datetime, timedelta

import ddt
from django.core.urlresolvers import reverse
import freezegun
from nose.plugins.attrib import attr
import pytz

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
            enrollment_mode=CourseMode.VERIFIED,
            days_till_verification_deadline=14,
            verification_status=None,
    ):
        """Set up the course and user for this test."""
        now = datetime.now(pytz.UTC)
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
                expiration_datetime=now + timedelta(days=days_till_upgrade_deadline)
            )
            CourseEnrollmentFactory.create(course_id=self.course.id, user=self.user, mode=enrollment_mode)
        else:
            CourseEnrollmentFactory.create(course_id=self.course.id, user=self.user)

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
        # Before course starts
        ({}, (CourseEndDate, CourseStartDate, TodaysDate, VerificationDeadlineDate, VerifiedUpgradeDeadlineDate)),
        # After course end
        ({'days_till_start': -10,
          'days_till_end': -5,
          'days_till_upgrade_deadline': -6,
          'days_till_verification_deadline': -5,
          'verification_status': 'approved'},
         (TodaysDate, CourseEndDate)),
        # No course end date
        ({'days_till_end': None},
         (CourseStartDate, TodaysDate, VerificationDeadlineDate, VerifiedUpgradeDeadlineDate)),
        # During course run
        ({'days_till_start': -1},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate, VerifiedUpgradeDeadlineDate)),
        # Verification approved
        ({'days_till_start': -10,
          'days_till_upgrade_deadline': -1,
          'days_till_verification_deadline': 1,
          'verification_status': 'approved'},
         (TodaysDate, CourseEndDate)),
        # After upgrade deadline
        ({'days_till_start': -10, 'days_till_upgrade_deadline': -1},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate)),
        # After verification deadline
        ({'days_till_start': -10,
          'days_till_upgrade_deadline': -2,
          'days_till_verification_deadline': -1},
         (TodaysDate, CourseEndDate, VerificationDeadlineDate))
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

    @freezegun.freeze_time('2015-01-02')
    def test_todays_date(self):
        self.setup_course_and_user()
        block = TodaysDate(self.course, self.user)
        self.assertTrue(block.is_enabled)
        self.assertEqual(block.date, datetime.now(pytz.UTC))
        self.assertEqual(block.title, 'Today is Jan 02, 2015 (00:00 UTC)')
        self.assertNotIn('date-summary-date', block.render())

    @freezegun.freeze_time('2015-01-02')
    def test_todays_date_render(self):
        self.setup_course_and_user()
        block = TodaysDate(self.course, self.user)
        self.assertIn('Jan 02, 2015', block.render())

    ## CourseStartDate

    def test_course_start_date(self):
        self.setup_course_and_user()
        block = CourseStartDate(self.course, self.user)
        self.assertEqual(block.date, self.course.start)

    @freezegun.freeze_time('2015-01-02')
    def test_start_date_render(self):
        self.setup_course_and_user()
        block = CourseStartDate(self.course, self.user)
        self.assertIn('in 1 day - Jan 03, 2015', block.render())

    ## CourseEndDate

    def test_course_end_date_during_course(self):
        self.setup_course_and_user(days_till_start=-1)
        block = CourseEndDate(self.course, self.user)
        self.assertEqual(
            block.description,
            'To earn a certificate, you must complete all requirements before this date.'
        )

    def test_course_end_date_after_course(self):
        self.setup_course_and_user(days_till_start=-2, days_till_end=-1)
        block = CourseEndDate(self.course, self.user)
        self.assertEqual(
            block.description,
            'This course is archived, which means you can review course content but it is no longer active.'
        )

    ## VerifiedUpgradeDeadlineDate

    @freezegun.freeze_time('2015-01-02')
    def test_verified_upgrade_deadline_date(self):
        self.setup_course_and_user(days_till_upgrade_deadline=1)
        block = VerifiedUpgradeDeadlineDate(self.course, self.user)
        self.assertEqual(block.date, datetime.now(pytz.UTC) + timedelta(days=1))
        self.assertEqual(block.link, reverse('verify_student_upgrade_and_verify', args=(self.course.id,)))

    def test_without_upgrade_deadline(self):
        self.setup_course_and_user(enrollment_mode=None)
        block = VerifiedUpgradeDeadlineDate(self.course, self.user)
        self.assertIsNone(block.date)

    ## VerificationDeadlineDate

    def test_no_verification_deadline(self):
        self.setup_course_and_user(days_till_start=-1, days_till_verification_deadline=None)
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertFalse(block.is_enabled)

    def test_no_verified_enrollment(self):
        self.setup_course_and_user(days_till_start=-1, enrollment_mode=CourseMode.AUDIT)
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertFalse(block.is_enabled)

    @freezegun.freeze_time('2015-01-02')
    def test_verification_deadline_date_upcoming(self):
        self.setup_course_and_user(days_till_start=-1)
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertEqual(block.css_class, 'verification-deadline-upcoming')
        self.assertEqual(block.title, 'Verification Deadline')
        self.assertEqual(block.date, datetime.now(pytz.UTC) + timedelta(days=14))
        self.assertEqual(
            block.description,
            'You must successfully complete verification before this date to qualify for a Verified Certificate.'
        )
        self.assertEqual(block.link_text, 'Verify My Identity')
        self.assertEqual(block.link, reverse('verify_student_verify_now', args=(self.course.id,)))

    @freezegun.freeze_time('2015-01-02')
    def test_verification_deadline_date_retry(self):
        self.setup_course_and_user(days_till_start=-1, verification_status='denied')
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertEqual(block.css_class, 'verification-deadline-retry')
        self.assertEqual(block.title, 'Verification Deadline')
        self.assertEqual(block.date, datetime.now(pytz.UTC) + timedelta(days=14))
        self.assertEqual(
            block.description,
            'You must successfully complete verification before this date to qualify for a Verified Certificate.'
        )
        self.assertEqual(block.link_text, 'Retry Verification')
        self.assertEqual(block.link, reverse('verify_student_reverify'))

    @freezegun.freeze_time('2015-01-02')
    def test_verification_deadline_date_denied(self):
        self.setup_course_and_user(
            days_till_start=-10,
            verification_status='denied',
            days_till_verification_deadline=-1,
        )
        block = VerificationDeadlineDate(self.course, self.user)
        self.assertEqual(block.css_class, 'verification-deadline-passed')
        self.assertEqual(block.title, 'Missed Verification Deadline')
        self.assertEqual(block.date, datetime.now(pytz.UTC) + timedelta(days=-1))
        self.assertEqual(
            block.description,
            "Unfortunately you missed this course's deadline for a successful verification."
        )
        self.assertEqual(block.link_text, 'Learn More')
        self.assertEqual(block.link, '')

    @freezegun.freeze_time('2015-01-02')
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
