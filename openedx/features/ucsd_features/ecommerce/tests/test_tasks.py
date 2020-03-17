"""
Test cases for celery tasks
"""
import httpretty

from django.conf import settings
from mock import patch

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory
from course_modes.tests.factories import CourseModeFactory

from openedx.features.ucsd_features.ecommerce.tasks import assign_course_voucher_to_user
from openedx.features.ucsd_features.ecommerce.tests.utils import make_ecommerce_url


class UCSDFeaturesEcommerceTasksTests(ModuleStoreTestCase):

    def setUp(self):
        super(UCSDFeaturesEcommerceTasksTests, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory()
        self.course_mode = CourseModeFactory.create(course_id=self.course.id, mode_slug='verified')

    @patch('openedx.features.ucsd_features.ecommerce.tasks.logger.error', autospec=True)
    def test_assign_course_voucher_to_user_when_no_user_exists(self, mocked_logger):
        invalid_user_email = 'doesnotexsts@mail.com'
        course_key = str(self.course.id)
        assign_course_voucher_to_user.apply(args=(invalid_user_email, course_key, self.course_mode.sku)).get()
        mocked_logger.assert_called_once_with('User with email: doesnotexsts@mail.com not found.'
                                              ' Cannot assign a voucher.')

    @httpretty.activate
    @patch('openedx.features.ucsd_features.ecommerce.tasks.logger.info', autospec=True)
    def test_assign_course_voucher_to_user_with_successful_assignment(self, mocked_logger):
        url = make_ecommerce_url('/ucsd/api/v1/assign_voucher/')
        httpretty.register_uri(
            httpretty.POST,
            url,
            status=200,
            body='{}',
            content_type='application/json'
        )
        course_key = str(self.course.id)
        assign_course_voucher_to_user.apply(args=(self.user.email, course_key, self.course_mode.sku)).get()

        expected_log_message = 'Successfully assigned a voucher to user {} for the course {}.'.format(
            self.user.username, course_key
        )
        mocked_logger.assert_called_once_with(expected_log_message)

    @httpretty.activate
    @patch('openedx.features.ucsd_features.ecommerce.tasks.logger.error', autospec=True)
    def test_assign_course_voucher_to_user_with_failed_assignment(self, mocked_logger):
        url = make_ecommerce_url('/ucsd/api/v1/assign_voucher/')
        httpretty.register_uri(
            httpretty.POST,
            url,
            status=400,
            body='{}',
            content_type='application/json'
        )
        course_key = str(self.course.id)
        assign_course_voucher_to_user.apply(args=(self.user.email, course_key, self.course_mode.sku)).get()
        expected_log_message = ('Failed to send request to assign a voucher to user'
                                ' {} for the course {}.\nError message: '
                                'Client Error 400: {}'.format(
                                    self.user.username,
                                    course_key,
                                    url
                                ))
        mocked_logger.assert_called_once_with(expected_log_message)
