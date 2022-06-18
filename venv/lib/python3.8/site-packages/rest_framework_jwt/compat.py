# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime
import sys

from django import VERSION
import jwt

from .settings import api_settings


try:
    from django.urls import include
except ImportError:
    from django.conf.urls import include  # noqa: F401


try:
  from django.conf.urls import url
except ImportError:
  from django.urls import re_path as url


if sys.version_info[0] == 2:
    # Use unicode-aware gettext on Python 2
    from django.utils.translation import ugettext_lazy as gettext_lazy
else:
    from django.utils.translation import gettext_lazy as gettext_lazy


try:
    from django.utils.encoding import smart_str
except ImportError:
    from django.utils.encoding import smart_text as smart_str


def has_set_cookie_samesite():
    return (VERSION >= (2,1,0))


def set_cookie_with_token(response, name, token):
    params = {
        'expires': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
        'domain': api_settings.JWT_AUTH_COOKIE_DOMAIN,
        'path': api_settings.JWT_AUTH_COOKIE_PATH,
        'secure': api_settings.JWT_AUTH_COOKIE_SECURE,
        'httponly': True
    }

    if has_set_cookie_samesite():
        params.update({'samesite': api_settings.JWT_AUTH_COOKIE_SAMESITE})

    response.set_cookie(name, token, **params)


if jwt.__version__.startswith("2"):
    jwt_version = 2
    ExpiredSignature = jwt.ExpiredSignatureError    
else:
    jwt_version = 1
    ExpiredSignature = jwt.ExpiredSignature

def jwt_decode(token, key, verify=None, **kwargs):
    if verify is not None:
        if jwt_version == 1:
            kwargs["verify"] = verify
        else:
            if "options" not in kwargs:
                kwargs["options"] = {"verify_signature": verify}
            else:
                kwargs["options"]["verify_signature"] = verify
    if jwt_version == 2 and "algorithms" not in kwargs:
        kwargs["algorithms"] = ["HS256"]
    return jwt.decode(token, key, **kwargs)