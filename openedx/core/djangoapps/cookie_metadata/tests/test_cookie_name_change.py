"""
Test Module to test CookieNameChange class
"""
from unittest.mock import Mock

from django.test import TestCase


from ..middleware import CookieNameChange


class TestCookieNameChange(TestCase):
    """
    Test class for CookieNameChange
    """

    def setUp(self):
        super().setUp()
        self.mock_response = Mock()
        self.cookie_name_change_middleware = CookieNameChange(self.mock_response)
        self.mock_request = Mock()

        self.old_value = "." * 100
        self.old_key = 'a'
        self.extra_cookies = {
            "_b": "." * 13,
            "_c_": "." * 13,
            "a.b": "." * 10,
        }
        self.old_dict = {
            self.old_key: self.old_value,
        }

        self.expand_settings = {
            "alternate": self.old_key,
            "current": "b",
        }

    def test_cookie_swap(self):
        """Check to make sure self.Middleware correctly swaps keys"""

        self.old_dict.update(self.extra_cookies)

        self.mock_request.COOKIES = self.old_dict.copy()

        with self.settings(
            COOKIE_NAME_CHANGE_ACTIVATE=True
        ), self.settings(COOKIE_NAME_CHANGE_EXPAND_INFO=self.expand_settings):
            self.cookie_name_change_middleware(self.mock_request)

        assert self.expand_settings["alternate"] not in self.mock_request.COOKIES.keys()
        assert self.expand_settings["current"] in self.mock_request.COOKIES.keys()
        assert self.mock_request.COOKIES[self.expand_settings["current"]] == self.old_value
        test_dict = self.extra_cookies.copy()
        test_dict[self.expand_settings['current']] = self.old_value
        assert self.mock_request.COOKIES == test_dict

        # make sure response function is called once
        self.mock_response.assert_called_once()

    def test_cookie_no_swap(self):
        """Make sure self.cookie_name_change_middleware does not change cookie if current cookie is already present"""

        new_value = "." * 13
        no_change_cookies = {
            self.expand_settings['current']: new_value,
            "_c_": "." * 13,
            "a.b": "." * 10,
        }

        self.old_dict.update(no_change_cookies)

        self.mock_request.COOKIES = self.old_dict.copy()

        with self.settings(
            COOKIE_NAME_CHANGE_ACTIVATE=True
        ), self.settings(COOKIE_NAME_CHANGE_EXPAND_INFO=self.expand_settings):
            self.cookie_name_change_middleware(self.mock_request)

        assert self.expand_settings["alternate"] not in self.mock_request.COOKIES.keys()
        assert self.expand_settings["current"] in self.mock_request.COOKIES.keys()
        assert self.mock_request.COOKIES[self.expand_settings["current"]] == new_value
        assert self.mock_request.COOKIES == no_change_cookies

        # make sure response function is called once
        self.mock_response.assert_called_once()

    def test_does_nothing(self):
        """Make sure turning off toggle turns off self.cookie_name_change_middleware"""

        new_value = "." * 13
        no_change_cookies = {
            self.expand_settings['current']: new_value,
            "_c_": "." * 13,
            "a.b": "." * 10,
        }
        self.old_dict.update(no_change_cookies)

        self.mock_request.COOKIES = self.old_dict.copy()

        with self.settings(
            COOKIE_NAME_CHANGE_ACTIVATE=False
        ), self.settings(COOKIE_NAME_CHANGE_EXPAND_INFO=self.expand_settings):
            self.cookie_name_change_middleware(self.mock_request)

        assert self.mock_request.COOKIES == self.old_dict

        # make sure response function is called once
        self.mock_response.assert_called_once()
