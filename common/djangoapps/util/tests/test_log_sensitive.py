"""
Tests for util.logging
"""

from common.djangoapps.util.log_sensitive import decrypt_log_message, encrypt_for_log, generate_reader_keys


def test_round_trip():
    reader_keys = generate_reader_keys()
    reader_public_64 = reader_keys['public']
    reader_private_64 = reader_keys['private']

    to_log = encrypt_for_log("Testing testing 1234", reader_public_64)
    # Something of roughly the correct form ("key|msg")
    assert '|' in to_log

    decrypted = decrypt_log_message(to_log, reader_private_64)
    assert decrypted == "Testing testing 1234"
