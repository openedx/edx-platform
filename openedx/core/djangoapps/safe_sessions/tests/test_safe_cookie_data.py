# pylint: disable=protected-access
"""
Unit tests for SafeCookieData
"""

import ddt
from django.test import TestCase
import itertools
from mock import patch
from time import time

from ..middleware import SafeCookieData, SafeCookieError
from .test_utils import TestSafeSessionsLogMixin


@ddt.ddt
class TestSafeCookieData(TestSafeSessionsLogMixin, TestCase):
    """
    Test class for SafeCookieData
    """
    def setUp(self):
        super(TestSafeCookieData, self).setUp()
        self.session_id = 'test_session_id'
        self.user_id = 'test_user_id'
        self.safe_cookie_data = SafeCookieData.create(self.session_id, self.user_id)

    def assert_cookie_data_equal(self, cookie_data1, cookie_data2):
        """
        Asserts equivalency of the given cookie datas by comparing
        their member variables.
        """
        self.assertDictEqual(cookie_data1.__dict__, cookie_data2.__dict__)

    #---- Test Success ----#

    @ddt.data(
        *itertools.product(
            ['test_session_id', '1', '100'],
            ['test_user_id', None, 0, 1, 100],
        )
    )
    @ddt.unpack
    def test_success(self, session_id, user_id):
        # create and verify
        safe_cookie_data_1 = SafeCookieData.create(session_id, user_id)
        self.assertTrue(safe_cookie_data_1.verify(user_id))

        # serialize
        serialized_value = unicode(safe_cookie_data_1)

        # parse and verify
        safe_cookie_data_2 = SafeCookieData.parse(serialized_value)
        self.assertTrue(safe_cookie_data_2.verify(user_id))

        # compare
        self.assert_cookie_data_equal(safe_cookie_data_1, safe_cookie_data_2)

    def test_version(self):
        self.assertEquals(self.safe_cookie_data.version, SafeCookieData.CURRENT_VERSION)

    def test_serialize(self):
        serialized_value = unicode(self.safe_cookie_data)
        for field_value in self.safe_cookie_data.__dict__.itervalues():
            self.assertIn(unicode(field_value), serialized_value)

    #---- Test Parse ----#

    @ddt.data(['1', 'session_id', 'key_salt', 'signature'], ['1', 's', 'k', 'sig'])
    def test_parse_success(self, cookie_data_fields):
        self.assert_cookie_data_equal(
            SafeCookieData.parse(SafeCookieData.SEPARATOR.join(cookie_data_fields)),
            SafeCookieData(*cookie_data_fields),
        )

    def test_parse_success_serialized(self):
        serialized_value = unicode(self.safe_cookie_data)
        self.assert_cookie_data_equal(
            SafeCookieData.parse(serialized_value),
            self.safe_cookie_data,
        )

    @ddt.data('1', '1|s', '1|s|k', '1|s|k|sig|extra', '73453', 's90sfs')
    def test_parse_error(self, serialized_value):
        with self.assert_parse_error():
            with self.assertRaises(SafeCookieError):
                SafeCookieData.parse(serialized_value)

    @ddt.data(0, 2, -1, 'invalid_version')
    def test_parse_invalid_version(self, version):
        serialized_value = '{}|session_id|key_salt|signature'.format(version)
        with self.assert_logged(r"SafeCookieData version .* is not supported."):
            with self.assertRaises(SafeCookieError):
                SafeCookieData.parse(serialized_value)

    #---- Test Create ----#

    @ddt.data(None, '')
    def test_create_invalid_session_id(self, session_id):
        with self.assert_invalid_session_id():
            with self.assertRaises(SafeCookieError):
                SafeCookieData.create(session_id, self.user_id)

    @ddt.data(None, '')
    def test_create_no_user_id(self, user_id):
        with self.assert_logged('SafeCookieData received empty user_id', 'warning'):
            safe_cookie_data = SafeCookieData.create(self.session_id, user_id)
            self.assertTrue(safe_cookie_data.verify(user_id))

    #---- Test Verify ----#

    def test_verify_success(self):
        self.assertTrue(self.safe_cookie_data.verify(self.user_id))

    #- Test verify: expiration -#

    def test_verify_expired_signature(self):
        three_weeks_from_now = time() + 60 * 60 * 24 * 7 * 3
        with patch('time.time', return_value=three_weeks_from_now):
            with self.assert_signature_error_logged('Signature age'):
                self.assertFalse(self.safe_cookie_data.verify(self.user_id))

    #- Test verify: incorrect user -#

    @ddt.data(None, 'invalid_user_id', -1)
    def test_verify_incorrect_user_id(self, user_id):
        with self.assert_incorrect_user_logged():
            self.assertFalse(self.safe_cookie_data.verify(user_id))

    @ddt.data('version', 'session_id')
    def test_verify_incorrect_field_value(self, field_name):
        setattr(self.safe_cookie_data, field_name, 'incorrect_cookie_value')
        with self.assert_incorrect_user_logged():
            self.assertFalse(self.safe_cookie_data.verify(self.user_id))

    #- Test verify: incorrect signature -#

    def test_verify_another_signature(self):
        another_cookie_data = SafeCookieData.create(self.session_id, self.user_id)  # different key_salt and expiration
        self.safe_cookie_data.signature = another_cookie_data.signature
        with self.assert_incorrect_signature_logged():
            self.assertFalse(self.safe_cookie_data.verify(self.user_id))

    def test_verify_incorrect_key_salt(self):
        self.safe_cookie_data.key_salt = 'incorrect_cookie_value'
        with self.assert_incorrect_signature_logged():
            self.assertFalse(self.safe_cookie_data.verify(self.user_id))

    @ddt.data(
        *itertools.product(
            range(0, 100, 25),
            range(5, 20, 5),
        )
    )
    @ddt.unpack
    def test_verify_corrupt_signed_data(self, start, length):

        def make_corrupt(signature, start, end):
            """
            Replaces characters in the given signature starting
            at the start offset until the end offset.
            """
            return signature[start:end] + 'x' * (end - start) + signature[end:]

        self.safe_cookie_data.signature = make_corrupt(
            self.safe_cookie_data.signature, start, start + length
        )
        with self.assert_incorrect_signature_logged():
            self.assertFalse(self.safe_cookie_data.verify(self.user_id))

    #- Test verify: corrupt signature -#

    def test_verify_corrupt_signature(self):
        self.safe_cookie_data.signature = 'corrupt_signature'
        with self.assert_signature_error_logged('No .* found in value'):
            self.assertFalse(self.safe_cookie_data.verify(self.user_id))

    #---- Test Digest ----#

    def test_digest_success(self):
        # Should return the same digest twice.
        self.assertEqual(
            self.safe_cookie_data._compute_digest(self.user_id),
            self.safe_cookie_data._compute_digest(self.user_id),
        )

    @ddt.data('another_user', 0, None)
    def test_digest_incorrect_user(self, incorrect_user):
        self.assertNotEqual(
            self.safe_cookie_data._compute_digest(self.user_id),
            self.safe_cookie_data._compute_digest(incorrect_user)
        )

    @ddt.data(
        *itertools.product(
            ['version', 'session_id'],
            ['incorrect_value', 0, None],
        )
    )
    @ddt.unpack
    def test_digest_incorrect_field_value(self, field_name, incorrect_field_value):
        digest = self.safe_cookie_data._compute_digest(self.user_id),
        setattr(self.safe_cookie_data, field_name, incorrect_field_value)
        self.assertNotEqual(
            digest,
            self.safe_cookie_data._compute_digest(self.user_id)
        )
