"""
Module that provides a connection to the ModuleStore specified in the django settings.

Passes settings.MODULESTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import
from importlib import import_module

from django.conf import settings

_MODULESTORE = None

FUNCTION_KEYS = ['render_template']


def load_function(path):
    """
    Load a function by name.

    path is a string of the form "path.to.module.function"
    returns the imported python object `function` from `path.to.module`
    """
    module_path, _, name = path.rpartition('.')
    return getattr(import_module(module_path), name)


def load_modulestore(config):
    class_ = load_function(config['ENGINE'])

    options = {}
    options.update(config['OPTIONS'])
    for key in FUNCTION_KEYS:
        if key in options:
            options[key] = load_function(options[key])

    return class_(**options)

# TODO why's this here v in modulestore.py?
def modulestore():
    """
    Find and return the correctly ModuleStore instance for this environment.
    """
    global _MODULESTORE
    if _MODULESTORE is None:
        if settings.MODULESTORE['ENGINE'] == 'xmodule.modulestore.comparison.ComparisonModuleStore':
            stores = [load_modulestore(cfg) for cfg in settings.MODULESTORE['stores']]
            class_ = load_function(settings.MODULESTORE['ENGINE'])
            _MODULESTORE = class_(*stores)
        else:
            class_ = load_function(settings.MODULESTORE['ENGINE'])

            options = {}

            options.update(settings.MODULESTORE['OPTIONS'])
            for key in FUNCTION_KEYS:
                if key in options:
                    options[key] = load_function(options[key])

            _MODULESTORE = class_(**options)

    return _MODULESTORE

# if 'DJANGO_SETTINGS_MODULE' in environ:
#     # Initialize the modulestores immediately
#     for store_name in settings.MODULESTORE:
#         modulestore(store_name)
