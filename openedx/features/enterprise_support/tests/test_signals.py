"""Tests of email marketing signal handlers."""
from __future__ import absolute_import

import logging

import ddt
from django.test import TestCase
from mock import patch
from student.tests.factories import UserFactory
from edx_django_utils.cache import TieredCache
from openedx.features.enterprise_support.tests.factories import (
    EnterpriseCourseEnrollmentFactory,
    EnterpriseCustomerFactory,
    EnterpriseCustomerUserFactory
)
from openedx.features.enterprise_support.utils import get_data_consent_share_cache_key

log = logging.getLogger(__name__)

LOGGER_NAME = "enterprise_support.signals"

TEST_EMAIL = "test@edx.org"


@ddt.ddt
class EnterpriseSupportSignals(TestCase):
    """
    Tests for the enterprise support signals.
    """

    def setUp(self):
        self.user = UserFactory.create(username='test', email=TEST_EMAIL)
        self.course_id = 'course-v1:edX+DemoX+Demo_Course'
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

    @patch('openedx.features.enterprise_support.signals.update_user.delay')
    def test_register_user(self, mock_update_user):
        """
        make sure marketing enterprise user call invokes update_user
        """
        enterprise_customer = EnterpriseCustomerFactory()
        EnterpriseCustomerUserFactory(
            user_id=self.user.id,
            enterprise_customer=enterprise_customer
        )
        mock_update_user.assert_called_with(
            sailthru_vars={
                'is_enterprise_learner': True,
                'enterprise_name': enterprise_customer.name,
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

        # Enrolling user to Course
        enterprise_customer_user = EnterpriseCustomerUserFactory(user_id=self.user.id)
        EnterpriseCourseEnrollmentFactory(
            course_id=self.course_id,
            enterprise_customer_user=enterprise_customer_user,
        )
        self.assertFalse(self._is_dsc_cache_found(self.user.id, self.course_id))

    def test_signal_update_dsc_cache_on_enterprise_customer_update(self):
        """
        make sure update_dsc_cache_on_enterprise_customer_update signal clears data_sharing_consent_needed cache after
         enable_data_sharing_consent flag is changed.
        """

        # Enrolling user to Course
        enterprise_customer = EnterpriseCustomerFactory()
        enterprise_customer_user = EnterpriseCustomerUserFactory(
            user_id=self.user.id,
            enterprise_customer=enterprise_customer
        )
        EnterpriseCourseEnrollmentFactory(
            course_id=self.course_id,
            enterprise_customer_user=enterprise_customer_user,
        )

        self._create_dsc_cache(self.user.id, self.course_id)
        self.assertTrue(self._is_dsc_cache_found(self.user.id, self.course_id))

        # updating enable_data_sharing_consent flag
        enterprise_customer.enable_data_sharing_consent = False
        enterprise_customer.save()

        self.assertFalse(self._is_dsc_cache_found(self.user.id, self.course_id))
