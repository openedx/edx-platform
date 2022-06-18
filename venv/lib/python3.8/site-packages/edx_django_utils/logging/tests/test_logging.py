"""
Tests for logging.
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from edx_django_utils.logging import RemoteIpFilter, UserIdFilter


class MockRecord:
    """
    Mocks a logging construct to receive data to be interpolated.
    """
    def __init__(self):
        self.userid = None
        self.remoteip = None


class TestLoggingFilters(TestCase):
    """
    Test the logging filters for users and IP addresses
    """

    @patch('edx_django_utils.logging.internal.filters.get_current_user')
    def test_userid_filter(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.pk = '1234'
        mock_get_user.return_value = mock_user

        user_filter = UserIdFilter()
        test_record = MockRecord()
        user_filter.filter(test_record)

        self.assertEqual(test_record.userid, '1234')

    def test_userid_filter_no_user(self):
        user_filter = UserIdFilter()
        test_record = MockRecord()
        user_filter.filter(test_record)

        self.assertEqual(test_record.userid, None)

    @patch('edx_django_utils.logging.internal.filters.get_current_request')
    def test_remoteip_filter(self, mock_get_request):
        mock_request = MagicMock()
        mock_request.META = {'REMOTE_ADDR': '192.168.1.1'}
        mock_get_request.return_value = mock_request

        ip_filter = RemoteIpFilter()
        test_record = MockRecord()
        ip_filter.filter(test_record)

        self.assertEqual(test_record.remoteip, '192.168.1.1')

    def test_remoteip_filter_no_request(self):
        ip_filter = RemoteIpFilter()
        test_record = MockRecord()
        ip_filter.filter(test_record)

        self.assertEqual(test_record.remoteip, None)
