"""
    Tests for enrollment refund capabilities.
"""
from datetime import datetime, timedelta
import ddt
import httpretty
import logging
import pytz
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings
from mock import patch

from student.models import CourseEnrollment, CourseEnrollmentAttribute
from student.tests.factories import UserFactory, CourseModeFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

# These imports refer to lms djangoapps.
# Their testcases are only run under lms.
from certificates.models import CertificateStatuses  # pylint: disable=import-error
from certificates.tests.factories import GeneratedCertificateFactory  # pylint: disable=import-error
from openedx.core.djangoapps.commerce.utils import ECOMMERCE_DATE_FORMAT

# Explicitly import the cache from ConfigurationModel so we can reset it after each test
from config_models.models import cache

log = logging.getLogger(__name__)
TEST_API_URL = 'http://www-internal.example.com/api'
TEST_API_SIGNING_KEY = 'edx'
JSON = 'application/json'


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class RefundableTest(SharedModuleStoreTestCase):
    """
    Tests for dashboard utility functions
    """

    @classmethod
    def setUpClass(cls):
        super(RefundableTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        """ Setup components used by each refund test."""
        super(RefundableTest, self).setUp()
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')
        self.verified_mode = CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='Verified',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        self.enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode='verified')

        self.client = Client()
        cache.clear()

    def test_refundable(self):
        """ Assert base case is refundable"""
        self.assertTrue(self.enrollment.refundable())

    def test_refundable_expired_verification(self):
        """ Assert that enrollment is not refundable if course mode has expired."""
        self.verified_mode.expiration_datetime = datetime.now(pytz.UTC) - timedelta(days=1)
        self.verified_mode.save()
        self.assertFalse(self.enrollment.refundable())

        # Assert that can_refund overrides this and allows refund
        self.enrollment.can_refund = True
        self.assertTrue(self.enrollment.refundable())

    def test_refundable_of_purchased_course(self):
        """ Assert that courses without a verified mode are not refundable"""
        self.client.login(username="jack", password="test")
        course = CourseFactory.create()
        CourseModeFactory.create(
            course_id=course.id,
            mode_slug='honor',
            min_price=10,
            currency='usd',
            mode_display_name='honor',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        enrollment = CourseEnrollment.enroll(self.user, course.id, mode='honor')

        # TODO: Until we can allow course administrators to define a refund period for paid for courses show_refund_option should be False. # pylint: disable=fixme
        self.assertFalse(enrollment.refundable())

        resp = self.client.post(reverse('student.views.dashboard', args=[]))
        self.assertIn('You will not be refunded the amount you paid.', resp.content)

    def test_refundable_when_certificate_exists(self):
        """ Assert that enrollment is not refundable once a certificat has been generated."""
        self.assertTrue(self.enrollment.refundable())

        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified'
        )

        self.assertFalse(self.enrollment.refundable())

        # Assert that can_refund overrides this and allows refund
        self.enrollment.can_refund = True
        self.assertTrue(self.enrollment.refundable())

    def test_refundable_with_cutoff_date(self):
        """ Assert enrollment is refundable before cutoff and not refundable after."""
        self.assertTrue(self.enrollment.refundable())

        with patch('student.models.CourseEnrollment.refund_cutoff_date') as cutoff_date:
            cutoff_date.return_value = datetime.now(pytz.UTC) - timedelta(minutes=5)
            self.assertFalse(self.enrollment.refundable())

            cutoff_date.return_value = datetime.now(pytz.UTC) + timedelta(minutes=5)
            self.assertTrue(self.enrollment.refundable())

    @ddt.data(
        (timedelta(days=1), timedelta(days=2), timedelta(days=2), 14),
        (timedelta(days=2), timedelta(days=1), timedelta(days=2), 14),
        (timedelta(days=1), timedelta(days=2), timedelta(days=2), 1),
        (timedelta(days=2), timedelta(days=1), timedelta(days=2), 1),
    )
    @ddt.unpack
    @httpretty.activate
    @override_settings(ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY, ECOMMERCE_API_URL=TEST_API_URL)
    def test_refund_cutoff_date(self, order_date_delta, course_start_delta, expected_date_delta, days):
        """
        Assert that the later date is used with the configurable refund period in calculating the returned cutoff date.
        """
        now = datetime.now(pytz.UTC).replace(microsecond=0)
        order_date = now + order_date_delta
        course_start = now + course_start_delta
        expected_date = now + expected_date_delta
        refund_period = timedelta(days=days)
        order_number = 'OSCR-1000'
        expected_content = '{{"date_placed": "{date}"}}'.format(date=order_date.strftime(ECOMMERCE_DATE_FORMAT))

        httpretty.register_uri(
            httpretty.GET,
            '{url}/orders/{order}/'.format(url=TEST_API_URL, order=order_number),
            status=200, body=expected_content,
            adding_headers={'Content-Type': JSON}
        )

        self.enrollment.course_overview.start = course_start
        self.enrollment.attributes.add(CourseEnrollmentAttribute(
            enrollment=self.enrollment,
            namespace='order',
            name='order_number',
            value=order_number
        ))

        with patch('student.models.EnrollmentRefundConfiguration.current') as config:
            instance = config.return_value
            instance.refund_window = refund_period
            self.assertEqual(
                self.enrollment.refund_cutoff_date(),
                expected_date + refund_period
            )

    def test_refund_cutoff_date_no_attributes(self):
        """ Assert that the None is returned when no order number attribute is found."""
        self.assertIsNone(self.enrollment.refund_cutoff_date())

    @httpretty.activate
    @override_settings(ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY, ECOMMERCE_API_URL=TEST_API_URL)
    def test_multiple_refunds_dashbaord_page_error(self):
        """ Order with mutiple refunds will not throw 500 error when dashboard page will access."""
        now = datetime.now(pytz.UTC).replace(microsecond=0)
        order_date = now + timedelta(days=1)
        order_number = 'OSCR-1000'
        expected_content = '{{"date_placed": "{date}"}}'.format(date=order_date.strftime(ECOMMERCE_DATE_FORMAT))

        httpretty.register_uri(
            httpretty.GET,
            '{url}/orders/{order}/'.format(url=TEST_API_URL, order=order_number),
            status=200, body=expected_content,
            adding_headers={'Content-Type': JSON}
        )

        # creating multiple attributes for same order.
        for attribute_count in range(2):  # pylint: disable=unused-variable
            self.enrollment.attributes.add(CourseEnrollmentAttribute(
                enrollment=self.enrollment,
                namespace='order',
                name='order_number',
                value=order_number
            ))

        self.client.login(username="jack", password="test")
        resp = self.client.post(reverse('student.views.dashboard', args=[]))
        self.assertEqual(resp.status_code, 200)
