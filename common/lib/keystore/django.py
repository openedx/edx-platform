"""
Module that provides a connection to the keystore specified in the django settings.

Passes settings.KEYSTORE as kwargs to MongoKeyStore
"""

from __future__ import absolute_import

from django.conf import settings
from .mongo import MongoKeyStore

_KEYSTORE = None


def keystore():
    global _KEYSTORE

    if _KEYSTORE is None:
        _KEYSTORE = MongoKeyStore(**settings.KEYSTORE)

    return _KEYSTORE
