"""
Module that provides a connection to the ModuleStore specified in the django settings.

Passes settings.MODULESTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import

from importlib import import_module

from django.conf import settings

_MODULESTORES = {}


def modulestore(name='default'):
    global _MODULESTORES

    if name not in _MODULESTORES:
        class_path = settings.MODULESTORE[name]['ENGINE']
        module_path, _, class_name = class_path.rpartition('.')
        class_ = getattr(import_module(module_path), class_name)
        _MODULESTORES[name] = class_(
            **settings.MODULESTORE[name]['OPTIONS'])

    return _MODULESTORES[name]
