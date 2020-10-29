"""
    Tests for enrollment refund capabilities.
"""


import logging
import unittest
from datetime import datetime, timedelta

import ddt
import httpretty
import pytz
# Explicitly import the cache from ConfigurationModel so we can reset it after each test
from config_models.models import cache
from django.conf import settings
from django.test.client import Client
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch
from six.moves import range

# These imports refer to lms djangoapps.
# Their testcases are only run under lms.
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.commerce.utils import ECOMMERCE_DATE_FORMAT
from common.djangoapps.student.models import CourseEnrollment, CourseEnrollmentAttribute, EnrollmentRefundConfiguration
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

log = logging.getLogger(__name__)
TEST_API_URL = 'http://www-internal.example.com/api'
JSON = 'application/json'


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class RefundableTest(SharedModuleStoreTestCase):
    """
    Tests for dashboard utility functions
    """
    USER_PASSWORD = 'test'
    ORDER_NUMBER = 'EDX-100000'

    @classmethod
    def setUpClass(cls):
        super(RefundableTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        """ Setup components used by each refund test."""
        super(RefundableTest, self).setUp()
        self.user = UserFactory.create(password=self.USER_PASSWORD)
        self.verified_mode = CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='Verified',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )

        self.enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode='verified')

        self.client = Client()
        cache.clear()

    @patch('common.djangoapps.student.models.CourseEnrollment.refund_cutoff_date')
    def test_refundable(self, cutoff_date):
        """ Assert base case is refundable"""
        cutoff_date.return_value = datetime.now(pytz.UTC) + timedelta(days=1)
        self.assertTrue(self.enrollment.refundable())

    @patch('common.djangoapps.student.models.CourseEnrollment.refund_cutoff_date')
    def test_refundable_expired_verification(self, cutoff_date):
        """ Assert that enrollment is refundable if course mode has expired."""
        cutoff_date.return_value = datetime.now(pytz.UTC) + timedelta(days=1)
        self.verified_mode.expiration_datetime = datetime.now(pytz.UTC) - timedelta(days=1)
        self.verified_mode.save()
        self.assertTrue(self.enrollment.refundable())

    @patch('common.djangoapps.student.models.CourseEnrollment.refund_cutoff_date')
    def test_refundable_when_certificate_exists(self, cutoff_date):
        """ Assert that enrollment is not refundable once a certificat has been generated."""

        cutoff_date.return_value = datetime.now(pytz.UTC) + timedelta(days=1)

        self.assertTrue(self.enrollment.refundable())

        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified'
        )

        self.assertFalse(self.enrollment.refundable())
        self.assertFalse(
            self.enrollment.refundable(
                user_already_has_certs_for=GeneratedCertificate.course_ids_with_certs_for_user(self.user)
            )
        )

        # Assert that can_refund overrides this and allows refund
        self.enrollment.can_refund = True
        self.assertTrue(self.enrollment.refundable())
        self.assertTrue(
            self.enrollment.refundable(
                user_already_has_certs_for=GeneratedCertificate.course_ids_with_certs_for_user(self.user)
            )
        )

    @patch('common.djangoapps.student.models.CourseEnrollment.refund_cutoff_date')
    def test_refundable_with_cutoff_date(self, cutoff_date):
        """ Assert enrollment is refundable before cutoff and not refundable after."""
        cutoff_date.return_value = datetime.now(pytz.UTC) + timedelta(days=1)
        self.assertTrue(self.enrollment.refundable())

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
    @override_settings(ECOMMERCE_API_URL=TEST_API_URL)
    def test_refund_cutoff_date(self, order_date_delta, course_start_delta, expected_date_delta, days):
        """
        Assert that the later date is used with the configurable refund period in calculating the returned cutoff date.
        """
        now = datetime.now(pytz.UTC).replace(microsecond=0)
        order_date = now + order_date_delta
        course_start = now + course_start_delta
        expected_date = now + expected_date_delta
        refund_period = timedelta(days=days)
        date_placed = order_date.strftime(ECOMMERCE_DATE_FORMAT)
        expected_content = '{{"date_placed": "{date}"}}'.format(date=date_placed)

        httpretty.register_uri(
            httpretty.GET,
            '{url}/orders/{order}/'.format(url=TEST_API_URL, order=self.ORDER_NUMBER),
            status=200, body=expected_content,
            adding_headers={'Content-Type': JSON}
        )

        self.enrollment.course_overview.start = course_start
        self.enrollment.attributes.create(
            enrollment=self.enrollment,
            namespace='order',
            name='order_number',
            value=self.ORDER_NUMBER
        )

        with patch('common.djangoapps.student.models.EnrollmentRefundConfiguration.current') as config:
            instance = config.return_value
            instance.refund_window = refund_period
            self.assertEqual(
                self.enrollment.refund_cutoff_date(),
                expected_date + refund_period
            )

            expected_date_placed_attr = {
                "namespace": "order",
                "name": "date_placed",
                "value": date_placed,
            }

            self.assertIn(
                expected_date_placed_attr,
                CourseEnrollmentAttribute.get_enrollment_attributes(self.enrollment)
            )

    def test_refund_cutoff_date_no_attributes(self):
        """ Assert that the None is returned when no order number attribute is found."""
        self.assertIsNone(self.enrollment.refund_cutoff_date())

    @patch('openedx.core.djangoapps.commerce.utils.ecommerce_api_client')
    def test_refund_cutoff_date_with_date_placed_attr(self, mock_ecommerce_api_client):
        """
        Assert that the refund_cutoff_date returns order placement date if order:date_placed
        attribute exist without calling ecommerce.
        """
        now = datetime.now(pytz.UTC).replace(microsecond=0)
        order_date = now + timedelta(days=2)
        course_start = now + timedelta(days=1)

        self.enrollment.course_overview.start = course_start
        self.enrollment.attributes.create(
            enrollment=self.enrollment,
            namespace='order',
            name='date_placed',
            value=order_date.strftime(ECOMMERCE_DATE_FORMAT)
        )

        refund_config = EnrollmentRefundConfiguration.current()
        self.assertEqual(
            self.enrollment.refund_cutoff_date(),
            order_date + refund_config.refund_window
        )
        mock_ecommerce_api_client.assert_not_called()

    @httpretty.activate
    @override_settings(ECOMMERCE_API_URL=TEST_API_URL)
    def test_multiple_refunds_dashbaord_page_error(self):
        """ Order with mutiple refunds will not throw 500 error when dashboard page will access."""
        now = datetime.now(pytz.UTC).replace(microsecond=0)
        order_date = now + timedelta(days=1)
        expected_content = '{{"date_placed": "{date}"}}'.format(date=order_date.strftime(ECOMMERCE_DATE_FORMAT))

        httpretty.register_uri(
            httpretty.GET,
            '{url}/orders/{order}/'.format(url=TEST_API_URL, order=self.ORDER_NUMBER),
            status=200, body=expected_content,
            adding_headers={'Content-Type': JSON}
        )

        # creating multiple attributes for same order.
        for attribute_count in range(2):  # pylint: disable=unused-variable
            self.enrollment.attributes.create(
                enrollment=self.enrollment,
                namespace='order',
                name='order_number',
                value=self.ORDER_NUMBER
            )

        self.client.login(username=self.user.username, password=self.USER_PASSWORD)
        resp = self.client.post(reverse('dashboard', args=[]))
        self.assertEqual(resp.status_code, 200)
