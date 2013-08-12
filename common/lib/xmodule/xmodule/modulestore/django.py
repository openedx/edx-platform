"""
Module that provides a connection to the ModuleStore specified in the django settings.

Passes settings.MODULESTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import
from importlib import import_module

from django.conf import settings
from xmodule.modulestore.loc_mapper_store import LocMapperStore

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

_loc_singleton = None
def loc_mapper():
    """
    Get the loc mapper which bidirectionally maps Locations to Locators. Used like modulestore() as
    a singleton accessor.
    """
    # pylint: disable=W0603
    global _loc_singleton
    # pylint: disable=W0212
    if _loc_singleton is None:
        # instantiate
        _loc_singleton = LocMapperStore(settings.modulestore_options)
    return _loc_singleton

