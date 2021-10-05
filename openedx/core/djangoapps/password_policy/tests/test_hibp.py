"""
Test 'have i been pwned' password service
"""


from unittest.mock import Mock, patch

from django.test import TestCase
from edx_toggles.toggles.testutils import override_waffle_switch
from requests.exceptions import ReadTimeout
from testfixtures import LogCapture

from openedx.core.djangoapps.password_policy.hibp import PwnedPasswordsAPI, log
from openedx.core.djangoapps.user_authn.config.waffle import ENABLE_PWNED_PASSWORD_API


class PwnedPasswordsAPITest(TestCase):
    """
    Tests pwned password service
    """
    @override_waffle_switch(ENABLE_PWNED_PASSWORD_API, True)
    @patch('requests.get')
    def test_matched_pwned_passwords(self, mock_get):
        """
        Test that pwned service returns pwned passwords dict
        """
        response_string = "7ecd77ecd7:341\r\n7ecd77ecd77ecd7:12"
        pwned_password = {
            "7ecd77ecd7": 341,
            "7ecd77ecd77ecd7": 12,
        }
        response = Mock()
        response.text = response_string
        mock_get.return_value = response
        response = PwnedPasswordsAPI.range('7ecd7')

        self.assertEqual(response, pwned_password)

    @override_waffle_switch(ENABLE_PWNED_PASSWORD_API, True)
    @patch('requests.get', side_effect=ReadTimeout)
    def test_warning_log_on_timeout(self, mock_get):  # pylint: disable=unused-argument
        """
        Test that captures the warning log on timeout
        """
        with LogCapture(log.name) as log_capture:
            PwnedPasswordsAPI.range('7ecd7')
            log_capture.check_present(
                (
                    log.name,
                    'WARNING',
                    'Request timed out for 7ecd7'
                )
            )
        assert 'Request timed out for 7ecd7' in log_capture.records[0].getMessage()
