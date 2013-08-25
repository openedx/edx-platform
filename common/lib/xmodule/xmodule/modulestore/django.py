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


def create_modulestore_instance(engine, options):
    """
    This will return a new instance of a modulestore given an engine and options
    """
    class_ = load_function(engine)

    _options = {}
    _options.update(options)

    for key in FUNCTION_KEYS:
        if key in _options and isinstance(_options[key], basestring):
            _options[key] = load_function(_options[key])

    return class_(
        **_options
    )


def modulestore(name='default'):
    """
    This returns an instance of a modulestore of given name. This will wither return an existing
    modulestore or create a new one
    """
    if name not in _MODULESTORES:
        _MODULESTORES[name] = create_modulestore_instance(settings.MODULESTORE[name]['ENGINE'],
                                                          settings.MODULESTORE[name]['OPTIONS'])

    return _MODULESTORES[name]


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


def clear_existing_modulestores():
    """
    Clear the existing modulestore instances, causing
    them to be re-created when accessed again.

    This is useful for flushing state between unit tests.
    """
    _MODULESTORES.clear()


def editable_modulestore(name='default'):
    """
    Retrieve a modulestore that we can modify.
    This is useful for tests that need to insert test
    data into the modulestore.

    Currently, only Mongo-backed modulestores can be modified.
    Returns `None` if no editable modulestore is available.
    """

    # Try to retrieve the ModuleStore
    # Depending on the settings, this may or may not
    # be editable.
    store = modulestore(name)

    # If this is a `MixedModuleStore`, then we will need
    # to retrieve the actual Mongo instance.
    # We assume that the default is Mongo.
    if hasattr(store, 'modulestores'):
        store = store.modulestores['default']

    # At this point, we either have the ability to create
    # items in the store, or we do not.
    if hasattr(store, 'create_xmodule'):
        return store

    else:
        return None
