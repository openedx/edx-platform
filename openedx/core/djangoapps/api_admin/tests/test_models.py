# pylint: disable=missing-docstring
import ddt
from django.test import TestCase

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest
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
