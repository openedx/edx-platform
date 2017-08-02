# -*- coding: utf-8 -*-
"""Tests for course home page date summary blocks."""
from datetime import datetime, timedelta

import ddt
from django.core.urlresolvers import reverse
from freezegun import freeze_time
from nose.plugins.attrib import attr
from pytz import utc

from commerce.models import CommerceConfiguration
from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from courseware.courses import get_course_date_blocks
from courseware.date_summary import (
    CourseEndDate,
    CourseStartDate,
    TodaysDate,
    VerificationDeadlineDate,
    VerifiedUpgradeDeadlineDate
)
from courseware.models import DynamicUpgradeDeadlineConfiguration, CourseDynamicUpgradeDeadlineConfiguration
from lms.djangoapps.verify_student.models import VerificationDeadline
from lms.djangoapps.verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.features.course_experience import UNIFIED_COURSE_TAB_FLAG
from student.tests.factories import CourseEnrollmentFactory, UserFactory, TEST_PASSWORD
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr(shard=1)
@ddt.ddt
class CourseDateSummaryTest(SharedModuleStoreTestCase):
    """Tests for course date summary blocks."""

    def setUp(self):
        super(CourseDateSummaryTest, self).setUp()
        SelfPacedConfiguration.objects.create(enable_course_home_improvements=True)

    def create_course_run(self, days_till_start=1, days_till_end=14, days_till_upgrade_deadline=4,
                          days_till_verification_deadline=14):
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

    def create_user(self, verification_status=None):
        """ Create a new User instance.

        Arguments:
            verification_status (str): User's verification status. If this value is set an instance of
                SoftwareSecurePhotoVerification will be created for the user with the specified status.
        """
        user = UserFactory()

        if verification_status is not None:
            SoftwareSecurePhotoVerificationFactory.create(user=user, status=verification_status)

        return user

    def test_course_info_feature_flag(self):
        SelfPacedConfiguration(enable_course_home_improvements=False).save()
        course = self.create_course_run()
        user = self.create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)

        self.client.login(username=user.username, password=TEST_PASSWORD)
        url = reverse('info', args=(course.id,))
        response = self.client.get(url)
        self.assertNotIn('date-summary', response.content)

    def test_course_info_logged_out(self):
        course = self.create_course_run()
        url = reverse('info', args=(course.id,))
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
        course = self.create_course_run(**course_kwargs)
        user = self.create_user(**user_kwargs)
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)
        self.assert_block_types(course, user, expected_blocks)

    @ddt.data(
        # Course not started
        ({}, (CourseStartDate, TodaysDate, CourseEndDate, VerifiedUpgradeDeadlineDate)),
        # Course active
        ({'days_till_start': -1}, (TodaysDate, CourseEndDate, VerifiedUpgradeDeadlineDate)),
        # Course ended
        ({'days_till_start': -10, 'days_till_end': -5},
         (TodaysDate, CourseEndDate, VerifiedUpgradeDeadlineDate)),
    )
    @ddt.unpack
    def test_enabled_block_types_without_enrollment(self, course_kwargs, expected_blocks):
        course = self.create_course_run(**course_kwargs)
        user = self.create_user()
        self.assert_block_types(course, user, expected_blocks)

    def test_enabled_block_types_with_non_upgradeable_course_run(self):
        course = self.create_course_run(days_till_start=-10, days_till_verification_deadline=None)
        user = self.create_user()
        CourseMode.objects.get(course_id=course.id, mode_slug=CourseMode.VERIFIED).delete()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.AUDIT)
        self.assert_block_types(course, user, (TodaysDate, CourseEndDate))

    def test_todays_date_block(self):
        """
        Helper function to test that today's date block renders correctly
        and displays the correct time, accounting for daylight savings
        """
        with freeze_time('2015-01-02'):
            course = self.create_course_run()
            user = self.create_user()
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
            course = self.create_course_run()
            user = self.create_user()
            self.client.login(username=user.username, password=TEST_PASSWORD)

            html_elements = [
                '<h3 class="hd hd-6 handouts-header">Important Course Dates</h3>',
                '<div class="date-summary-container">',
                '<div class="date-summary date-summary-todays-date">',
                '<span class="hd hd-6 heading localized-datetime"',
                'data-datetime="2015-01-02 00:00:00+00:00"',
                'data-string="Today is {date}"',
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
            course = self.create_course_run()
            user = self.create_user()
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
                'data-string="Today is {date}"',
                'data-timezone="America/Los_Angeles"'
            ]
            for html in html_elements:
                self.assertContains(response, html)

    ## Tests Course Start Date
    def test_course_start_date(self):
        course = self.create_course_run()
        user = self.create_user()
        block = CourseStartDate(course, user)
        self.assertEqual(block.date, course.start)

    @ddt.data(
        'info',
        'openedx.course_experience.course_home',
    )
    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
    def test_start_date_render(self, url_name):
        with freeze_time('2015-01-02'):
            course = self.create_course_run()
            user = self.create_user()
            self.client.login(username=user.username, password=TEST_PASSWORD)
            url = reverse(url_name, args=(course.id,))
            response = self.client.get(url, follow=True)
            html_elements = [
                'data-string="in 1 day - {date}"',
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
            course = self.create_course_run()
            user = self.create_user()
            self.client.login(username=user.username, password=TEST_PASSWORD)
            set_user_preference(user, 'time_zone', 'America/Los_Angeles')
            url = reverse(url_name, args=(course.id,))
            response = self.client.get(url, follow=True)
            html_elements = [
                'data-string="in 1 day - {date}"',
                'data-datetime="2015-01-03 00:00:00+00:00"',
                'data-timezone="America/Los_Angeles"'
            ]
            for html in html_elements:
                self.assertContains(response, html)

    ## Tests Course End Date Block
    def test_course_end_date_for_certificate_eligible_mode(self):
        course = self.create_course_run(days_till_start=-1)
        user = self.create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)
        block = CourseEndDate(course, user)
        self.assertEqual(
            block.description,
            'To earn a certificate, you must complete all requirements before this date.'
        )

    def test_course_end_date_for_non_certificate_eligible_mode(self):
        course = self.create_course_run(days_till_start=-1)
        user = self.create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.AUDIT)
        block = CourseEndDate(course, user)
        self.assertEqual(
            block.description,
            'After this date, course content will be archived.'
        )
        self.assertEqual(block.title, 'Course End')

    def test_course_end_date_after_course(self):
        course = self.create_course_run(days_till_start=-2, days_till_end=-1)
        user = self.create_user()
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
        course = self.create_course_run()
        user = self.create_user()
        course_mode = CourseMode.objects.get(course_id=course.id, mode_slug=CourseMode.VERIFIED)
        course_mode.sku = sku
        course_mode.save()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)

        block = VerifiedUpgradeDeadlineDate(course, user)
        self.assertEqual(block.link, '{}?sku={}'.format(configuration.MULTIPLE_ITEMS_BASKET_PAGE_URL, sku))

    ## VerificationDeadlineDate
    def test_no_verification_deadline(self):
        course = self.create_course_run(days_till_start=-1, days_till_verification_deadline=None)
        user = self.create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)
        block = VerificationDeadlineDate(course, user)
        self.assertFalse(block.is_enabled)

    def test_no_verified_enrollment(self):
        course = self.create_course_run(days_till_start=-1)
        user = self.create_user()
        CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.AUDIT)
        block = VerificationDeadlineDate(course, user)
        self.assertFalse(block.is_enabled)

    def test_verification_deadline_date_upcoming(self):
        with freeze_time('2015-01-02'):
            course = self.create_course_run(days_till_start=-1)
            user = self.create_user()
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
            course = self.create_course_run(days_till_start=-1)
            user = self.create_user(verification_status='denied')
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
            course = self.create_course_run(days_till_start=-10, days_till_verification_deadline=-1)
            user = self.create_user(verification_status='denied')
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
        (-1, '1 day ago - {date}'),
        (1, 'in 1 day - {date}')
    )
    @ddt.unpack
    def test_render_date_string_past(self, delta, expected_date_string):
        with freeze_time('2015-01-02'):
            course = self.create_course_run(days_till_start=-10, days_till_verification_deadline=delta)
            user = self.create_user(verification_status='denied')
            CourseEnrollmentFactory(course_id=course.id, user=user, mode=CourseMode.VERIFIED)

            block = VerificationDeadlineDate(course, user)
            self.assertEqual(block.relative_datestring, expected_date_string)

    def create_self_paced_course_run(self, **kwargs):
        defaults = {
            'days_till_upgrade_deadline': 100,
        }
        defaults.update(kwargs)

        course = self.create_course_run(**defaults)
        course.self_paced = True
        self.store.update_item(course, None)
        overview = CourseOverview.get_from_id(course.id)
        self.assertTrue(overview.self_paced)

        return course

    def assert_upgrade_deadline(self, course, expected):
        """ Asserts the VerifiedUpgradeDeadlineDate block's date matches the expected value. """
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        self.assertEqual(block.date, expected)

    def test_date_with_self_paced_with_enrollment_before_course_start(self):
        """ Enrolling before a course begins should result in the upgrade deadline being set relative to the
        course start date. """
        global_config = DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        course = self.create_self_paced_course_run(days_till_start=3)
        overview = CourseOverview.get_from_id(course.id)
        expected = overview.start + timedelta(days=global_config.deadline_days)
        self.assert_upgrade_deadline(course, expected)

    def test_date_with_self_paced_with_enrollment_after_course_start(self):
        """ Enrolling after a course begins should result in the upgrade deadline being set relative to the
        enrollment date. """
        global_config = DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        course = self.create_self_paced_course_run(days_till_start=-1)
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        expected = enrollment.created + timedelta(days=global_config.deadline_days)
        self.assertEqual(block.date, expected)

        # Courses should be able to override the deadline
        course_config = CourseDynamicUpgradeDeadlineConfiguration.objects.create(
            enabled=True, course_id=course.id, opt_out=False, deadline_days=3
        )
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        expected = enrollment.created + timedelta(days=course_config.deadline_days)
        self.assertEqual(block.date, expected)

    def test_date_with_self_paced_without_dynamic_upgrade_deadline(self):
        """ Disabling the dynamic upgrade deadline functionality should result in the verified mode's
        expiration date being returned. """
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=False)
        course = self.create_self_paced_course_run()
        expected = CourseMode.objects.get(course_id=course.id, mode_slug=CourseMode.VERIFIED).expiration_datetime
        self.assert_upgrade_deadline(course, expected)

    def test_date_with_self_paced_with_course_opt_out(self):
        """ If the course run has opted out of the dynamic deadline, the course mode's deadline should be used. """
        course = self.create_self_paced_course_run(days_till_start=-1)
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        CourseDynamicUpgradeDeadlineConfiguration.objects.create(enabled=True, course_id=course.id, opt_out=True)
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)

        block = VerifiedUpgradeDeadlineDate(course, enrollment.user)
        expected = CourseMode.objects.get(course_id=course.id, mode_slug=CourseMode.VERIFIED).expiration_datetime
        self.assertEqual(block.date, expected)
