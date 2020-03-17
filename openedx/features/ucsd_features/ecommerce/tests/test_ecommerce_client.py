"""
Test cases for celery tasks
"""
import httpretty

from django.conf import settings
from mock import patch

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory

from openedx.features.ucsd_features.ecommerce.ecommerce_client import EcommerceRestAPIClient
from openedx.features.ucsd_features.ecommerce.tests.utils import make_ecommerce_url


class UCSDFeaturesEcommerceClientTests(ModuleStoreTestCase):

    def setUp(self):
        super(UCSDFeaturesEcommerceClientTests, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory()
        self.client = EcommerceRestAPIClient(self.user)

    @httpretty.activate
    def test_assign_voucher_to_user_with_success_response(self):
        url = make_ecommerce_url('/ucsd/api/v1/assign_voucher/')
        course_key = str(self.course.id)

        httpretty.register_uri(
            httpretty.POST,
            url,
            status=200,
            body='{}',
            content_type='application/json'
        )
        is_successfull, message = self.client.assign_voucher_to_user(self.user, course_key)
        self.assertTrue(is_successfull)
        self.assertEqual(message, '')

    @httpretty.activate
    @patch('openedx.features.ucsd_features.ecommerce.ecommerce_client.logger.exception', autospec=True)
    def test_assign_voucher_to_user_with_failure_response(self, mocked_logger):
        url = make_ecommerce_url('/ucsd/api/v1/assign_voucher/')
        course_key = str(self.course.id)

        httpretty.register_uri(
            httpretty.POST,
            url,
            status=400,
            body='{}',
            content_type='application/json'
        )

        is_successfull, message = self.client.assign_voucher_to_user(self.user, course_key)
        expected_message = 'Client Error 400: {}'.format(url)
        expected_logged_exception = ('Got failure response from ecommerce while '
                                     'trying to assign a voucher to user.\n'
                                     'Details:{}'.format(expected_message))
        self.assertFalse(is_successfull)
        self.assertEqual(message, expected_message)
        mocked_logger.assert_called_with(expected_logged_exception)

    @httpretty.activate
    def test_check_coupon_availability_for_course_with_success_response(self):
        url = make_ecommerce_url('/ucsd/api/v1/check_course_coupon/')
        course_key = str(self.course.id)

        httpretty.register_uri(
            httpretty.POST,
            url,
            status=200,
            body='{}',
            content_type='application/json'
        )

        is_successfull = self.client.check_coupon_availability_for_course(course_key)
        self.assertTrue(is_successfull)

    @httpretty.activate
    @patch('openedx.features.ucsd_features.ecommerce.ecommerce_client.logger.exception', autospec=True)
    def test_check_coupon_availability_for_course_with_failure_response(self, mocked_logger):
        url = make_ecommerce_url('/ucsd/api/v1/check_course_coupon/')
        course_key = str(self.course.id)

        httpretty.register_uri(
            httpretty.POST,
            url,
            status=400,
            body='{}',
            content_type='application/json'
        )

        expected_exception = 'Client Error 400: {}'.format(url)
        expected_logged_exception = ('Got failure response from ecommerce while '
                                     'trying to check coupon availability for the course.\n'
                                     'Details:{}'.format(expected_exception))

        is_successfull = self.client.check_coupon_availability_for_course(course_key)
        self.assertFalse(is_successfull)
        mocked_logger.assert_called_with(expected_logged_exception)
