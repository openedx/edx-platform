"""
Module that provides a connection to the keystore specified in the django settings.

Passes settings.KEYSTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import

from importlib import import_module

from django.conf import settings

_KEYSTORES = {}


def keystore(name='default'):
    global _KEYSTORES

    if name not in _KEYSTORES:
        class_path = settings.KEYSTORE[name]['ENGINE']
        module_path, _, class_name = class_path.rpartition('.')
        class_ = getattr(import_module(module_path), class_name)
        _KEYSTORES[name] = class_(
            **settings.KEYSTORE[name]['OPTIONS'])

    return _KEYSTORES[name]
