import jwt
from django.conf import settings
from django.test import TestCase

from openedx.features.edly.utils import encode_edly_user_info_cookie, decode_edly_user_info_cookie


class UtilsTests(TestCase):
    """
    Tests for utility methods.
    """

    def setUp(self):
        """
        Setup initial test data
        """
        self.test_edly_user_info_cookie_data = {
            'edly-org': 'edly',
            'edly-sub-org': 'cloud',
            'edx-org': 'cloudX'
        }

    def test_encode_edly_user_info_cookie(self):
        """
        Test that "encode_edly_user_info_cookie" method encodes data correctly.
        """
        actual_encoded_string = encode_edly_user_info_cookie(self.test_edly_user_info_cookie_data)
        expected_encoded_string = jwt.encode(self.test_edly_user_info_cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithm=settings.EDLY_JWT_ALGORITHM)
        assert actual_encoded_string == expected_encoded_string

    def test_decode_edly_user_info_cookie(self):
        """
        Test that "decode_edly_user_info_cookie" method decodes data correctly.
        """
        encoded_data = jwt.encode(self.test_edly_user_info_cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithm=settings.EDLY_JWT_ALGORITHM)
        decoded_edly_user_info_cookie_data = decode_edly_user_info_cookie(encoded_data)
        assert self.test_edly_user_info_cookie_data == decoded_edly_user_info_cookie_data
