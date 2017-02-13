"""
Test that testing utils do what they say.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http.request import HttpRequest
from django.test import TestCase
from waffle.models import Switch

from ..utils import get_mock_request, toggle_switch

USER_MODEL = get_user_model()


class TestGetMockRequest(TestCase):
    """
    Validate the behavior of get_mock_request
    """
    def test_mock_request_is_request(self):
        request = get_mock_request(USER_MODEL())
        self.assertIsInstance(request, HttpRequest)

    def test_user_is_attached_to_mock_request(self):
        user = USER_MODEL()
        request = get_mock_request(user)
        self.assertIs(request.user, user)

    def test_mock_request_without_user(self):
        request = get_mock_request()
        self.assertIsInstance(request.user, AnonymousUser)


class TestToggleSwitch(TestCase):
    """
    Verify that the toggle_switch utility can be used to turn Waffle Switches
    on and off.
    """
    def test_toggle_switch(self):
        """Verify that a new switch can be turned on and off."""
        name = 'foo'

        switch = toggle_switch(name)

        # Verify that the switch was saved.
        self.assertEqual(switch, Switch.objects.get())

        # Verify that the switch has the right name and is active.
        self.assertEqual(switch.name, name)
        self.assertTrue(switch.active)

        switch = toggle_switch(name)

        # Verify that the switch has been turned off.
        self.assertFalse(switch.active)
