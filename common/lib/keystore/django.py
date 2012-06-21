"""
Module that provides a connection to the keystore specified in the django settings.

Passes settings.KEYSTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import

from django.conf import settings
from .mongo import MongoModuleStore

_KEYSTORES = {}


def keystore(name='default'):
    global _KEYSTORES

    if name not in _KEYSTORES:
        _KEYSTORES[name] = MongoModuleStore(**settings.KEYSTORE[name])

    return _KEYSTORES[name]
