"""
Module that provides a connection to the keystore specified in the django settings.

Passes settings.KEYSTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import

from django.conf import settings
from .mongo import MongoModuleStore
from raw_module import RawDescriptor

_KEYSTORES = {}


def keystore(name='default'):
    global _KEYSTORES

    if name not in _KEYSTORES:
        # TODO (cpennington): Load the default class from a string
        _KEYSTORES[name] = MongoModuleStore(
            default_class=RawDescriptor,
            **settings.KEYSTORE[name])

    return _KEYSTORES[name]
