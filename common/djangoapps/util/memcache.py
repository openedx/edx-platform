"""
This module provides a KEY_FUNCTION suitable for use with a memcache backend
so that we can cache any keys, not just ones that memcache would ordinarily accept
"""
from django.utils.encoding import smart_str
import hashlib
import urllib


def fasthash(string):
    m = hashlib.new("md4")
    m.update(string)
    return m.hexdigest()


def safe_key(key, key_prefix, version):
    safe_key = urllib.quote_plus(smart_str(key))

    if len(safe_key) > 250:
        safe_key = fasthash(safe_key)

    return ":".join([key_prefix, str(version), safe_key])
