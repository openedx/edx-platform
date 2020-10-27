"""
Tests the ``generate_jwt_signing_key`` management command.
"""
# pylint: disable=missing-docstring
import sys
from contextlib import contextmanager
from StringIO import StringIO

import ddt
from mock import patch

from django.core.management import call_command
from django.test import TestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms


COMMAND_NAME = 'generate_jwt_signing_key'
LOGGER = 'openedx.core.djangoapps.oauth_dispatch.management.commands.generate_jwt_signing_key.log.info'
TEST_KEY_IDENTIFIER = 'some_key_identifier'


@skip_unless_lms
@ddt.ddt
class TestGenerateJwtSigningKey(TestCase):
    """
    Tests the ``generate_jwt_signing_key`` management command.
    """
    @contextmanager
    def _captured_output(self):
        new_out, new_err = StringIO(), StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = new_out, new_err
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = old_out, old_err

    def _assert_log_message(self, mock_log, message, expected_to_exist):
        log_message_exists = any(
            message in log_entry[0][0]
            for log_entry in mock_log.call_args_list
        )
        self.assertEqual(log_message_exists, expected_to_exist)

    def _assert_key_output(self, output_stream):
        expected_in_output = (
            'EDXAPP_JWT_PRIVATE_SIGNING_JWK', 'EDXAPP_JWT_SIGNING_ALGORITHM', 'COMMON_JWT_PUBLIC_SIGNING_JWK_SET'
        )
        for expected in expected_in_output:
            self.assertIn(expected, output_stream.getvalue())

    def _assert_presence_of_old_keys(self, mock_log, add_previous_public_keys):
        self._assert_log_message(mock_log, 'Old JWT_PUBLIC_SIGNING_JWK_SET', expected_to_exist=add_previous_public_keys)

    def _assert_presence_of_key_id(self, mock_log, output_stream, provide_key_id, key_id_size):
        if provide_key_id:
            self.assertIn(TEST_KEY_IDENTIFIER, output_stream.getvalue())
        else:
            self.assertNotIn(TEST_KEY_IDENTIFIER, output_stream.getvalue())
            key_id = mock_log.call_args_list[0][0][1]
            self.assertEqual(len(key_id), key_id_size or 8)

    @ddt.data(
        dict(add_previous_public_keys=True, provide_key_id=False, key_id_size=None),
        dict(add_previous_public_keys=True, provide_key_id=False, key_id_size=16),
        dict(add_previous_public_keys=False, provide_key_id=True, key_id_size=None),
    )
    @ddt.unpack
    def test_command(self, add_previous_public_keys, provide_key_id, key_id_size):
        command_options = dict(add_previous_public_keys=add_previous_public_keys)
        if provide_key_id:
            command_options['key_id'] = TEST_KEY_IDENTIFIER
        if key_id_size:
            command_options['key_id_size'] = key_id_size

        with self._captured_output() as (output_stream, _):
            with patch(LOGGER) as mock_log:
                call_command(COMMAND_NAME, **command_options)

        self._assert_key_output(output_stream)
        self._assert_presence_of_old_keys(mock_log, add_previous_public_keys)
        self._assert_presence_of_key_id(mock_log, output_stream, provide_key_id, key_id_size)
