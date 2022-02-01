"""
Tests for util.logging
"""

import re
from common.djangoapps.util.log_sensitive import decrypt_log_message, encrypt_for_log, generate_reader_keys


def test_encryption_round_trip():
    reader_keys = generate_reader_keys()
    reader_public_64 = reader_keys['public']
    reader_private_64 = reader_keys['private']

    to_log = encrypt_for_log("Testing testing 1234", reader_public_64)
    re_base64 = r'[a-zA-Z0-9/+=]'
    assert re.fullmatch(f'\\[encrypted: {re_base64}+\\|{re_base64}+\\]', to_log)

    to_decrypt = to_log.partition('[encrypted: ')[2].rstrip(']')

    decrypted = decrypt_log_message(to_decrypt, reader_private_64)
    assert decrypted == "Testing testing 1234"

    # Also check that decryption still works if someone accidentally
    # copies in the trailing framing "]" character, just as a
    # nice-to-have. (base64 module should handle this already, since
    # it stops reading at the first invalid base64 character.)
    decrypted_again = decrypt_log_message(to_decrypt + ']', reader_private_64)
    assert decrypted_again == "Testing testing 1234"
