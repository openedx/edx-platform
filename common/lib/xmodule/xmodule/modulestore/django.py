"""
Module that provides a connection to the ModuleStore specified in the django settings.

Passes settings.MODULESTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import
from importlib import import_module

from django.conf import settings
from django.core.cache import get_cache, InvalidCacheBackendError
from django.dispatch import Signal
from xmodule.modulestore.loc_mapper_store import LocMapperStore

# We may not always have the request_cache module available
try:
    from request_cache.middleware import RequestCache
    HAS_REQUEST_CACHE = True
except ImportError:
    HAS_REQUEST_CACHE = False

_MODULESTORES = {}

FUNCTION_KEYS = ['render_template']

def get_default_modulestore_name():
    """
    Returns the name of the default mongo module store
    IMPORTANT, this function can be (and is!) overloaded by middleware to help resolve
    between preview.hostname and www.hostname
    """
    return 'default'

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

    if HAS_REQUEST_CACHE:
        request_cache = RequestCache.get_request_cache()
    else:
        request_cache = None

    try:
        metadata_inheritance_cache = get_cache('mongo_metadata_inheritance')
    except InvalidCacheBackendError:
        metadata_inheritance_cache = get_cache('default')

    return class_(
        metadata_inheritance_cache_subsystem=metadata_inheritance_cache,
        request_cache=request_cache,
        modulestore_update_signal=Signal(providing_args=['modulestore', 'course_id', 'location']),
        xblock_mixins=getattr(settings, 'XBLOCK_MIXINS', ()),
        **_options
    )


def modulestore(name=None):
    """
    This returns an instance of a modulestore of given name. This will wither return an existing
    modulestore or create a new one
    """

    if not name:
        # If caller did not specify name then we should
        # use the default value
        name = get_default_modulestore_name()

    if name not in _MODULESTORES:
        _MODULESTORES[name] = create_modulestore_instance(settings.MODULESTORE[name]['ENGINE'],
                                                          settings.MODULESTORE[name]['OPTIONS'])
        # inject loc_mapper into newly created modulestore if it needs it
        if name == 'split' and _loc_singleton is not None:
            _MODULESTORES['split'].loc_mapper = _loc_singleton

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
        _loc_singleton = LocMapperStore(**settings.DOC_STORE_CONFIG)
    # inject into split mongo modulestore
    if 'split' in _MODULESTORES:
        _MODULESTORES['split'].loc_mapper = _loc_singleton
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
