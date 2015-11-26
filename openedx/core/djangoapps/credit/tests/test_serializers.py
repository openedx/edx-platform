""" Tests for Credit API serializers. """

# pylint: disable=no-member
from __future__ import unicode_literals

from django.test import TestCase

from openedx.core.djangoapps.credit import serializers
from openedx.core.djangoapps.credit.tests.factories import CreditProviderFactory, CreditEligibilityFactory
from student.tests.factories import UserFactory


class CreditProviderSerializerTests(TestCase):
    """ CreditProviderSerializer tests. """

    def test_data(self):
        """ Verify the correct fields are serialized. """
        provider = CreditProviderFactory(active=False)
        serializer = serializers.CreditProviderSerializer(provider)
        expected = {
            'id': provider.provider_id,
            'display_name': provider.display_name,
            'url': provider.provider_url,
            'status_url': provider.provider_status_url,
            'description': provider.provider_description,
            'enable_integration': provider.enable_integration,
            'fulfillment_instructions': provider.fulfillment_instructions,
            'thumbnail_url': provider.thumbnail_url,
        }
        self.assertDictEqual(serializer.data, expected)


class CreditEligibilitySerializerTests(TestCase):
    """ CreditEligibilitySerializer tests. """

    def test_data(self):
        """ Verify the correct fields are serialized. """
        user = UserFactory()
        eligibility = CreditEligibilityFactory(username=user.username)
        serializer = serializers.CreditEligibilitySerializer(eligibility)
        expected = {
            'course_key': unicode(eligibility.course.course_key),
            'deadline': eligibility.deadline.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'username': user.username,
        }
        self.assertDictEqual(serializer.data, expected)
