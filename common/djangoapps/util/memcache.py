"""
This module provides a KEY_FUNCTION suitable for use with a memcache backend
so that we can cache any keys, not just ones that memcache would ordinarily accept
"""


import hashlib
from urllib.parse import quote_plus

from django.utils.encoding import smart_str


def fasthash(string):
    """
    Hashes `string` into a string representation of a 128-bit digest.
    """
    md4 = hashlib.new("md4")
    md4.update(string.encode('utf-8'))
    return md4.hexdigest()


def cleaned_string(val):
    """
    Converts `val` to unicode and URL-encodes special characters
    (including quotes and spaces)
    """
    return quote_plus(smart_str(val))


def safe_key(key, key_prefix, version):
    """
    Given a `key`, `key_prefix`, and `version`,
    return a key that is safe to use with memcache.

    `key`, `key_prefix`, and `version` can be numbers, strings, or unicode.
    """

    # Clean for whitespace and control characters, which
    # cause memcache to raise an exception
    key = cleaned_string(key)
    key_prefix = cleaned_string(key_prefix)
    version = cleaned_string(version)

    # Attempt to combine the prefix, version, and key
    combined = ":".join([key_prefix, version, key])

    # If the total length is too long for memcache, hash it
    if len(combined) > 250:
        combined = fasthash(combined)

    # Return the result
    return combined
