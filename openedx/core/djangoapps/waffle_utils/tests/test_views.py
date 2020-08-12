"""
Tests for waffle utils views.
"""
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from student.tests.factories import UserFactory

from ..views import ToggleStateView


class ToggleStateViewTests(TestCase):

    def test_success_for_staff(self):
        response = self._get_toggle_state_response(is_staff=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)

    def test_failure_for_non_staff(self):
        response = self._get_toggle_state_response(is_staff=False)
        self.assertEqual(response.status_code, 403)

    def _get_toggle_state_response(self, is_staff=True):
        request = APIRequestFactory().get('/api/toggles/state/')
        user = UserFactory()
        user.is_staff = is_staff
        request.user = user
        view = ToggleStateView.as_view()
        response = view(request)
        return response
