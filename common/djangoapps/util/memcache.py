"""
This module provides a KEY_FUNCTION suitable for use with a memcache backend
so that we can cache any keys, not just ones that memcache would ordinarily accept
"""


import hashlib
from urllib.parse import quote_plus

from django.conf import settings
from django.utils.encoding import smart_str
from edx_django_utils.monitoring.utils import increment


def fasthash(string):
    """
    Hashes `string` into a string representation of a 128-bit digest.
    """
    if settings.FEATURES.get("ENABLE_BLAKE2B_HASHING", False):
        hash_obj = hashlib.new("blake2b", digest_size=16)
    else:
        hash_obj = hashlib.new("md4")
    hash_obj.update(string.encode('utf-8'))
    return hash_obj.hexdigest()


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

    # Temporary: Add observability to large-key hashing to help us
    # understand the safety of a cutover from md4 to blake2b hashing.
    # See https://github.com/edx/edx-arch-experiments/issues/872
    increment('memcache.safe_key.called')

    # If the total length is too long for memcache, hash it
    if len(combined) > 250:
        combined = fasthash(combined)
        # Temporary: See
        # https://github.com/edx/edx-arch-experiments/issues/872 and
        # previous comment.
        increment('memcache.safe_key.hash_large')

    # Return the result
    return combined
