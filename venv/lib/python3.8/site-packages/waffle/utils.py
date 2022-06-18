import hashlib

from django.conf import settings
from django.core.cache import caches

import waffle
from waffle import defaults


def get_setting(name, default=None):
    try:
        return getattr(settings, 'WAFFLE_' + name)
    except AttributeError:
        return getattr(defaults, name, default)


def keyfmt(k, v=None):
    prefix = get_setting('CACHE_PREFIX') + waffle.__version__
    if v is None:
        key = prefix + k
    else:
        key = prefix + hashlib.md5((k % v).encode('utf-8')).hexdigest()
    return key


def get_cache():
    CACHE_NAME = get_setting('CACHE_NAME')
    return caches[CACHE_NAME]
