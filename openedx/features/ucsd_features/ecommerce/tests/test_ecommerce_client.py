"""
Test cases for celery tasks
"""
import httpretty

from django.conf import settings
from mock import patch

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory

from openedx.features.ucsd_features.ecommerce.EcommerceClient import EcommerceRestAPIClient
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
        self.assertEqual(is_successfull, True)
        self.assertEqual(message, '')

    @httpretty.activate
    @patch('openedx.features.ucsd_features.ecommerce.EcommerceClient.logger.error', autospec=True)
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
        self.assertEqual(is_successfull, False)
        self.assertEqual(message, expected_message)
