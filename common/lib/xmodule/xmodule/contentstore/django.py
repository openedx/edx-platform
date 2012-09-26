from __future__ import absolute_import
from importlib import import_module
from os import environ

from django.conf import settings

_CONTENTSTORE = None

def load_function(path):
    """
    Load a function by name.

    path is a string of the form "path.to.module.function"
    returns the imported python object `function` from `path.to.module`
    """
    module_path, _, name = path.rpartition('.')
    return getattr(import_module(module_path), name)


def contentstore():
    global _CONTENTSTORE

    if _CONTENTSTORE is None:
        class_ = load_function(settings.CONTENTSTORE['ENGINE'])
        options = {}
        options.update(settings.CONTENTSTORE['OPTIONS'])
        _CONTENTSTORE = class_(**options)

    return _CONTENTSTORE
