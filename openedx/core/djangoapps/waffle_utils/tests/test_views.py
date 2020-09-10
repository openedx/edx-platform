"""
Tests for waffle utils views.
"""
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from waffle.testutils import override_switch

from student.tests.factories import UserFactory

from .. import WaffleFlag, WaffleFlagNamespace, WaffleSwitch, WaffleSwitchNamespace
from ..views import ToggleStateView
from ..testutils import override_waffle_flag

TEST_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace('test')
TEST_WAFFLE_FLAG = WaffleFlag(TEST_WAFFLE_FLAG_NAMESPACE, 'flag', __name__)


# TODO: Missing coverage for:
# - course overrides
# - computed_status
class ToggleStateViewTests(TestCase):

    def test_success_for_staff(self):
        response = self._get_toggle_state_response(is_staff=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)

    def test_failure_for_non_staff(self):
        response = self._get_toggle_state_response(is_staff=False)
        self.assertEqual(response.status_code, 403)

    @override_waffle_flag(TEST_WAFFLE_FLAG, True)
    def test_response_with_waffle_flag(self):
        response = self._get_toggle_state_response(is_staff=True)
        self.assertIn('waffle_flags', response.data)
        self.assertTrue(response.data['waffle_flags'])
        # This is no longer the first flag
        #self.assertEqual(response.data['waffle_flags'][0]['name'], 'test.flag')

    @override_switch('test.switch', True)
    def test_response_with_waffle_switch(self):
        response = self._get_toggle_state_response(is_staff=True)
        self.assertIn('waffle_switches', response.data)
        self.assertTrue(response.data['waffle_switches'])
        # This is no longer the first switch
        #self.assertEqual(response.data['waffle_switches'][0]['name'], 'test.switch')

    def _get_toggle_state_response(self, is_staff=True):
        request = APIRequestFactory().get('/api/toggles/state/')
        user = UserFactory()
        user.is_staff = is_staff
        request.user = user
        view = ToggleStateView.as_view()
        response = view(request)
        return response
