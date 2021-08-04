"""
Test Modle to test CookieNameChange class
"""
from unittest.mock import Mock

from django.test import TestCase


from ..middleware import CookieNameChange


class TestCookieNameChange(TestCase):
    """
    Test class for CookieNameChange
    """

    def test_cookie_swap(self):
        """Check to make sure Middleware correctly swaps keys"""

        mock_response = Mock()
        middleware = CookieNameChange(mock_response)
        mock_request = Mock()

        old_value = "." * 100
        extra_cookies = {
            "_b": "." * 13,
            "_c_": "." * 13,
            "a.b": "." * 10,
        }
        old_dict = {
            "a": old_value,
        }
        old_dict.update(extra_cookies)

        mock_request.COOKIES = old_dict.copy()
        expand_settings = {
            "old_name": "a",
            "new_name": "b",
            "old_domain": "old_domain.com",
        }

        with self.settings(
            COOKIE_NAME_CHANGE_ACTIVATE_EXPAND_PHASE=True
        ), self.settings(COOKIE_NAME_CHANGE_EXPAND_INFO=expand_settings):
            middleware(mock_request)

        assert expand_settings["old_name"] not in mock_request.COOKIES.keys()
        assert expand_settings["new_name"] in mock_request.COOKIES.keys()
        assert mock_request.COOKIES[expand_settings["new_name"]] == old_value
        test_dict = extra_cookies.copy()
        test_dict[expand_settings['new_name']] = old_value
        assert mock_request.COOKIES == test_dict

        # make sure response function is called once
        mock_response.assert_called_once()

    def test_cookie_no_swap(self):
        """Make sure middleware does not change cookie if new_name cookie is already present"""

        expand_settings = {
            "old_name": "a",
            "new_name": "b",
            "old_domain": "old_domain.com",
        }

        mock_response = Mock()
        middleware = CookieNameChange(mock_response)

        mock_request = Mock()

        old_value = "." * 100
        new_value = "." * 13
        no_change_cookies = {
            expand_settings['new_name']: new_value,
            "_c_": "." * 13,
            "a.b": "." * 10,
        }
        old_dict = {
            "a": old_value,
        }
        old_dict.update(no_change_cookies)

        mock_request.COOKIES = old_dict.copy()


        with self.settings(
            COOKIE_NAME_CHANGE_ACTIVATE_EXPAND_PHASE=True
        ), self.settings(COOKIE_NAME_CHANGE_EXPAND_INFO=expand_settings):
            middleware(mock_request)

        assert expand_settings["old_name"] not in mock_request.COOKIES.keys()
        assert expand_settings["new_name"] in mock_request.COOKIES.keys()
        assert mock_request.COOKIES[expand_settings["new_name"]] == new_value
        assert mock_request.COOKIES == no_change_cookies

        # make sure response function is called once
        mock_response.assert_called_once()

    def test_does_nothing(self):
        """Make sure turning off toggle turns off middleware"""

        expand_settings = {
            "old_name": "a",
            "new_name": "b",
            "old_domain": "old_domain.com",
        }

        mock_response = Mock()
        middleware = CookieNameChange(mock_response)

        mock_request = Mock()

        old_value = "." * 100
        new_value = "." * 13
        no_change_cookies = {
            expand_settings['new_name']: new_value,
            "_c_": "." * 13,
            "a.b": "." * 10,
        }
        old_dict = {
            "a": old_value,
        }
        old_dict.update(no_change_cookies)

        mock_request.COOKIES = old_dict.copy()


        with self.settings(
            COOKIE_NAME_CHANGE_ACTIVATE_EXPAND_PHASE=False
        ), self.settings(COOKIE_NAME_CHANGE_EXPAND_INFO=expand_settings):
            middleware(mock_request)

        assert mock_request.COOKIES == old_dict

        # make sure response function is called once
        mock_response.assert_called_once()
