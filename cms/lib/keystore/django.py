"""
Module that provides a connection to the keystore specified in the django settings.

Passes settings.KEYSTORE as kwargs to MongoKeyStore
"""

from __future__ import absolute_import

from django.conf import settings
from .mongo import MongoKeyStore

keystore = MongoKeyStore(**settings.KEYSTORE)
