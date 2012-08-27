"""
Module that provides a connection to the ModuleStore specified in the django settings.

Passes settings.MODULESTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import
from importlib import import_module
from os import environ

from django.conf import settings

_MODULESTORES = {}

FUNCTION_KEYS = ['render_template']


def load_function(path):
    """
    Load a function by name.

    path is a string of the form "path.to.module.function"
    returns the imported python object `function` from `path.to.module`
    """
    module_path, _, name = path.rpartition('.')
    return getattr(import_module(module_path), name)


def modulestore(name='default'):
    global _MODULESTORES

    if name not in _MODULESTORES:
        class_ = load_function(settings.MODULESTORE[name]['ENGINE'])

        options = {}
        options.update(settings.MODULESTORE[name]['OPTIONS'])
        for key in FUNCTION_KEYS:
            if key in options:
                options[key] = load_function(options[key])

        _MODULESTORES[name] = class_(
            **options
        )

    return _MODULESTORES[name]

# if 'DJANGO_SETTINGS_MODULE' in environ:
#     # Initialize the modulestores immediately
#     for store_name in settings.MODULESTORE:
#         modulestore(store_name)
