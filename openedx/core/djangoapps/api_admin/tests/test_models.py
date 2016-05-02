# pylint: disable=missing-docstring
import ddt
from django.db import IntegrityError
from django.test import TestCase

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest, ApiAccessConfig
from openedx.core.djangoapps.api_admin.tests.factories import ApiAccessRequestFactory
from student.tests.factories import UserFactory


@ddt.ddt
class ApiAccessRequestTests(TestCase):

    def setUp(self):
        super(ApiAccessRequestTests, self).setUp()
        self.user = UserFactory()
        self.request = ApiAccessRequestFactory(user=self.user)

    def test_default_status(self):
        self.assertEqual(self.request.status, ApiAccessRequest.PENDING)
        self.assertFalse(ApiAccessRequest.has_api_access(self.user))

    def test_approve(self):
        self.request.approve()  # pylint: disable=no-member
        self.assertEqual(self.request.status, ApiAccessRequest.APPROVED)

    def test_deny(self):
        self.request.deny()  # pylint: disable=no-member
        self.assertEqual(self.request.status, ApiAccessRequest.DENIED)

    def test_nonexistent_request(self):
        """Test that users who have not requested API access do not get it."""
        other_user = UserFactory()
        self.assertFalse(ApiAccessRequest.has_api_access(other_user))

    @ddt.data(
        (ApiAccessRequest.PENDING, False),
        (ApiAccessRequest.DENIED, False),
        (ApiAccessRequest.APPROVED, True),
    )
    @ddt.unpack
    def test_has_access(self, status, should_have_access):
        self.request.status = status
        self.request.save()  # pylint: disable=no-member
        self.assertEqual(ApiAccessRequest.has_api_access(self.user), should_have_access)

    def test_unique_per_user(self):
        with self.assertRaises(IntegrityError):
            ApiAccessRequestFactory(user=self.user)

    def test_no_access(self):
        self.request.delete()  # pylint: disable=no-member
        self.assertIsNone(ApiAccessRequest.api_access_status(self.user))

    def test_unicode(self):
        request_unicode = unicode(self.request)
        self.assertIn(self.request.website, request_unicode)  # pylint: disable=no-member
        self.assertIn(self.request.status, request_unicode)


class ApiAccessConfigTests(TestCase):

    def test_unicode(self):
        self.assertEqual(
            unicode(ApiAccessConfig(enabled=True)),
            u'ApiAccessConfig [enabled=True]'
        )
        self.assertEqual(
            unicode(ApiAccessConfig(enabled=False)),
            u'ApiAccessConfig [enabled=False]'
        )
