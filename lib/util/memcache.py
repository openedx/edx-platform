"""
This module provides a KEY_FUNCTION suitable for use with a memcache backend
so that we can cache any keys, not just ones that memcache would ordinarily accept
"""
from django.utils.hashcompat import md5_constructor
from django.utils.encoding import smart_str
import string

def safe_key(key, key_prefix, version):
    safe_key = smart_str(key)
    for char in safe_key:
        if ord(char) < 33 or ord(char) == 127:
            safe_key = safe_key.replace(char, '_')

    if len(safe_key) > 250:
        safe_key = md5_constructor(safe_key)

    return ":".join([key_prefix, str(version), safe_key])
