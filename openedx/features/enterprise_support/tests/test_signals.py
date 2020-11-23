"""Tests of email marketing signal handlers."""


import logging
from datetime import timedelta

import ddt
from django.test.utils import override_settings
from django.utils.timezone import now
from edx_django_utils.cache import TieredCache
from mock import patch
from opaque_keys.edx.keys import CourseKey
from slumber.exceptions import HttpClientError, HttpServerError
from testfixtures import LogCapture

from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.certificates.signals import listen_for_passing_grade
from openedx.core.djangoapps.commerce.utils import ECOMMERCE_DATE_FORMAT
from openedx.core.djangoapps.credit.tests.test_api import TEST_ECOMMERCE_WORKER
from openedx.core.djangoapps.signals.signals import COURSE_GRADE_NOW_PASSED
from openedx.features.enterprise_support.tests import FEATURES_WITH_ENTERPRISE_ENABLED
from openedx.features.enterprise_support.tests.factories import (
    EnterpriseCourseEnrollmentFactory,
    EnterpriseCustomerFactory,
    EnterpriseCustomerUserFactory
)
from openedx.features.enterprise_support.utils import get_data_consent_share_cache_key
from common.djangoapps.student.models import CourseEnrollmentAttribute
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

log = logging.getLogger(__name__)

LOGGER_NAME = "openedx.features.enterprise_support.signals"

TEST_EMAIL = "test@edx.org"


@ddt.ddt
@override_settings(FEATURES=FEATURES_WITH_ENTERPRISE_ENABLED)
@override_settings(ECOMMERCE_SERVICE_WORKER_USERNAME=TEST_ECOMMERCE_WORKER)
class EnterpriseSupportSignals(SharedModuleStoreTestCase):
    """
    Tests for the enterprise support signals.
    """

    def setUp(self):
        UserFactory.create(username=TEST_ECOMMERCE_WORKER)
        self.user = UserFactory.create(username='test', email=TEST_EMAIL)
        self.course_id = 'course-v1:edX+DemoX+Demo_Course'
        self.enterprise_customer = EnterpriseCustomerFactory()
        super(EnterpriseSupportSignals, self).setUp()

    @staticmethod
    def _create_dsc_cache(user_id, course_id):
        consent_cache_key = get_data_consent_share_cache_key(user_id, course_id)
        TieredCache.set_all_tiers(consent_cache_key, 0)

    @staticmethod
    def _is_dsc_cache_found(user_id, course_id):
        consent_cache_key = get_data_consent_share_cache_key(user_id, course_id)
        data_sharing_consent_needed_cache = TieredCache.get_cached_response(consent_cache_key)
        return data_sharing_consent_needed_cache.is_found

    def _create_enterprise_enrollment(self, user_id, course_id):
        """
        Create enterprise user and enrollment
        """
        enterprise_customer_user = EnterpriseCustomerUserFactory(
            user_id=user_id,
            enterprise_customer=self.enterprise_customer
        )
        EnterpriseCourseEnrollmentFactory(
            course_id=course_id,
            enterprise_customer_user=enterprise_customer_user,
        )

    @patch('openedx.features.enterprise_support.signals.update_user.delay')
    def test_register_user(self, mock_update_user):
        """
        make sure marketing enterprise user call invokes update_user
        """
        self._create_enterprise_enrollment(self.user.id, self.course_id)
        mock_update_user.assert_called_with(
            sailthru_vars={
                'is_enterprise_learner': True,
                'enterprise_name': self.enterprise_customer.name,
            },
            email=self.user.email
        )

    def test_signal_update_dsc_cache_on_course_enrollment(self):
        """
        make sure update_dsc_cache_on_course_enrollment signal clears cache when Enterprise Course Enrollment
        takes place
        """

        self._create_dsc_cache(self.user.id, self.course_id)
        self.assertTrue(self._is_dsc_cache_found(self.user.id, self.course_id))

        self._create_enterprise_enrollment(self.user.id, self.course_id)
        self.assertFalse(self._is_dsc_cache_found(self.user.id, self.course_id))

    def test_signal_update_dsc_cache_on_enterprise_customer_update(self):
        """
        make sure update_dsc_cache_on_enterprise_customer_update signal clears data_sharing_consent_needed cache after
         enable_data_sharing_consent flag is changed.
        """

        self._create_enterprise_enrollment(self.user.id, self.course_id)
        self._create_dsc_cache(self.user.id, self.course_id)
        self.assertTrue(self._is_dsc_cache_found(self.user.id, self.course_id))

        # updating enable_data_sharing_consent flag
        self.enterprise_customer.enable_data_sharing_consent = False
        self.enterprise_customer.save()

        self.assertFalse(self._is_dsc_cache_found(self.user.id, self.course_id))

    def _create_enrollment_to_refund(self, no_of_days_placed=10, enterprise_enrollment_exists=True):
        """Create enrollment to refund. """
        date_placed = now() - timedelta(days=no_of_days_placed)
        course = CourseFactory.create(display_name='test course', run="Testing_course", start=date_placed)
        enrollment = CourseEnrollmentFactory(
            course_id=course.id,
            user=self.user,
            mode="verified",
        )
        CourseModeFactory.create(course_id=course.id, mode_slug='verified')
        CourseEnrollmentAttribute.objects.create(
            enrollment=enrollment,
            name='date_placed',
            namespace='order',
            value=date_placed.strftime(ECOMMERCE_DATE_FORMAT)
        )
        CourseEnrollmentAttribute.objects.create(
            enrollment=enrollment,
            name='order_number',
            namespace='order',
            value='EDX-000000001'
        )

        if enterprise_enrollment_exists:
            self._create_enterprise_enrollment(self.user.id, course.id)

        return enrollment

    @ddt.data(
        (True, True, 2, False),  # test if skip_refund
        (False, True, 20, False),  # test refundable time passed
        (False, False, 2, False),    # test not enterprise enrollment
        (False, True, 2, True),    # success: no skip_refund, is enterprise enrollment and still in refundable window.
    )
    @ddt.unpack
    def test_refund_order_voucher(self, skip_refund, enterprise_enrollment_exists, no_of_days_placed, api_called):
        """Test refund_order_voucher signal"""
        enrollment = self._create_enrollment_to_refund(no_of_days_placed, enterprise_enrollment_exists)
        with patch('openedx.features.enterprise_support.signals.ecommerce_api_client') as mock_ecommerce_api_client:
            enrollment.update_enrollment(is_active=False, skip_refund=skip_refund)
            self.assertEqual(mock_ecommerce_api_client.called, api_called)

    @ddt.data(
        (HttpClientError, 'INFO'),
        (HttpServerError, 'ERROR'),
        (Exception, 'ERROR'),
    )
    @ddt.unpack
    def test_refund_order_voucher_with_client_errors(self, mock_error, log_level):
        """Test refund_order_voucher signal client_error"""
        enrollment = self._create_enrollment_to_refund()
        with patch('openedx.features.enterprise_support.signals.ecommerce_api_client') as mock_ecommerce_api_client:
            client_instance = mock_ecommerce_api_client.return_value
            client_instance.enterprise.coupons.create_refunded_voucher.post.side_effect = mock_error()
            with LogCapture(LOGGER_NAME) as logger:
                enrollment.update_enrollment(is_active=False)
                self.assertEqual(mock_ecommerce_api_client.called, True)
                logger.check(
                    (
                        LOGGER_NAME,
                        log_level,
                        'Encountered {} from ecommerce while creating refund voucher. '
                        'Order=EDX-000000001, enrollment={}, user={}'.format(
                            mock_error.__name__, enrollment, enrollment.user
                        ),
                    )
                )

    def test_handle_enterprise_learner_passing_grade(self):
        """
        Test to assert transmit_single_learner_data is called when COURSE_GRADE_NOW_PASSED signal is fired
        """
        with patch(
            'integrated_channels.integrated_channel.tasks.transmit_single_learner_data.apply_async',
            return_value=None
        ) as mock_task_apply:
            course_key = CourseKey.from_string(self.course_id)
            COURSE_GRADE_NOW_PASSED.disconnect(dispatch_uid='new_passing_learner')
            COURSE_GRADE_NOW_PASSED.send(sender=None, user=self.user, course_id=course_key)
            self.assertFalse(mock_task_apply.called)

            self._create_enterprise_enrollment(self.user.id, self.course_id)
            task_kwargs = {
                'username': self.user.username,
                'course_run_id': self.course_id
            }
            COURSE_GRADE_NOW_PASSED.send(sender=None, user=self.user, course_id=course_key)
            mock_task_apply.assert_called_once_with(kwargs=task_kwargs)
            COURSE_GRADE_NOW_PASSED.connect(listen_for_passing_grade, dispatch_uid='new_passing_learner')
