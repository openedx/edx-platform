"""
Tests for custom enterprise_support Serializers.
"""
from unittest.mock import patch, MagicMock
from uuid import uuid4

from django.test import TestCase
from enterprise.models import LicensedEnterpriseCourseEnrollment

from openedx.features.enterprise_support.serializers import EnterpriseCourseEnrollmentSerializer
from openedx.features.enterprise_support.tests.factories import (
    EnterpriseCourseEnrollmentFactory,
    EnterpriseCustomerUserFactory
)


class EnterpriseCourseEnrollmentSerializerTests(TestCase):
    """
    Tests for EnterpriseCourseEnrollmentSerializer.
    """

    def setup_patch(self, function_name, return_value):
        """
        Patch a function with a given return value, and return the mock
        """
        mock = MagicMock(return_value=return_value)
        new_patch = patch(function_name, new=mock)
        new_patch.start()
        self.addCleanup(new_patch.stop)
        return mock

    def setUp(self):
        self.mock_pathways_with_course = self.setup_patch(
            'learner_pathway_progress.signals.get_learner_pathways_associated_with_course',
            None,
        )
        enterprise_customer_user = EnterpriseCustomerUserFactory()
        enterprise_course_enrollment = EnterpriseCourseEnrollmentFactory(
            enterprise_customer_user=enterprise_customer_user
        )
        self.enterprise_customer_user = enterprise_customer_user
        self.enterprise_course_enrollment = enterprise_course_enrollment

        super().setUp()

    def test_data_with_license(self):
        """ Verify the correct fields are serialized when the enrollment is licensed. """

        license_uuid = uuid4()
        licensed_ece = LicensedEnterpriseCourseEnrollment(
            license_uuid=license_uuid,
            enterprise_course_enrollment=self.enterprise_course_enrollment
        )
        licensed_ece.save()

        serializer = EnterpriseCourseEnrollmentSerializer(self.enterprise_course_enrollment)

        expected = {
            'enterprise_customer_name': self.enterprise_customer_user.enterprise_customer.name,
            'enterprise_customer_user_id': self.enterprise_customer_user.id,
            'course_id': self.enterprise_course_enrollment.course_id,
            'saved_for_later': self.enterprise_course_enrollment.saved_for_later,
            'license': {
                'uuid': str(license_uuid),
                'is_revoked': licensed_ece.is_revoked,
            }
        }
        self.assertDictEqual(serializer.data, expected)

    def test_data_without_license(self):
        """ Verify the correct fields are serialized when the enrollment is not licensed. """

        serializer = EnterpriseCourseEnrollmentSerializer(self.enterprise_course_enrollment)

        expected = {
            'enterprise_customer_name': self.enterprise_customer_user.enterprise_customer.name,
            'enterprise_customer_user_id': self.enterprise_customer_user.id,
            'course_id': self.enterprise_course_enrollment.course_id,
            'saved_for_later': self.enterprise_course_enrollment.saved_for_later,
            'license': None
        }
        self.assertDictEqual(serializer.data, expected)
