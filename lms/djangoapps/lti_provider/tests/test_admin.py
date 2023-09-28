"""
Tests for the LTI Provider's Admin Views
"""
from unittest.mock import Mock

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from lms.djangoapps.lti_provider.admin import LtiConsumerAdmin
from lms.djangoapps.lti_provider.models import LtiConsumer


class LtiConsumerAdminTests(TestCase):
    """
    Test the customizations applied for the LtiConsumerAdmin
    """
    def setUp(self):
        self.site = AdminSite()
        self.consumer = LtiConsumer(
            consumer_name="Test Consumer",
            consumer_key="test-key",
            consumer_secret="secret",
        )
        self.consumer.save()

    def test_lticonsumeradmin_read_only_fields(self):
        ma = LtiConsumerAdmin(LtiConsumer, self.site)
        request = Mock()

        self.assertEqual(ma.get_readonly_fields(request, None), ())
        self.assertEqual(ma.get_readonly_fields(request, self.consumer), ('auto_link_users_using_email',))
