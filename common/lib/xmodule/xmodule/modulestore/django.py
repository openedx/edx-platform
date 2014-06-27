"""
Module that provides a connection to the ModuleStore specified in the django settings.

Passes settings.MODULESTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import
from importlib import import_module
import re

from django.conf import settings
from django.core.cache import get_cache, InvalidCacheBackendError
import django.utils

from xmodule.modulestore.loc_mapper_store import LocMapperStore
from xmodule.util.django import get_current_request_hostname


# We may not always have the request_cache module available
try:
    from request_cache.middleware import RequestCache
    HAS_REQUEST_CACHE = True
except ImportError:
    HAS_REQUEST_CACHE = False

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


def create_modulestore_instance(engine, doc_store_config, options, i18n_service=None):
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
        xblock_mixins=getattr(settings, 'XBLOCK_MIXINS', ()),
        xblock_select=getattr(settings, 'XBLOCK_SELECT_FUNCTION', None),
        doc_store_config=doc_store_config,
        i18n_service=i18n_service or ModuleI18nService(),
        **_options
    )


def get_default_store_name_for_current_request():
    """
    This method will return the appropriate default store mapping for the current Django request,
    else 'default' which is the system default
    """
    store_name = 'default'

    # see what request we are currently processing - if any at all - and get hostname for the request
    hostname = get_current_request_hostname()

    # get mapping information which is defined in configurations
    mappings = getattr(settings, 'HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS', None)

    # compare hostname against the regex expressions set of mappings
    # which will tell us which store name to use
    if hostname and mappings:
        for key in mappings.keys():
            if re.match(key, hostname):
                store_name = mappings[key]
                return store_name

    return store_name


def modulestore(name=None):
    """
    This returns an instance of a modulestore of given name. This will wither return an existing
    modulestore or create a new one
    """

    if not name:
        # If caller did not specify name then we should
        # determine what should be the default
        name = get_default_store_name_for_current_request()

    if name not in _MODULESTORES:
        _MODULESTORES[name] = create_modulestore_instance(
            settings.MODULESTORE[name]['ENGINE'],
            settings.MODULESTORE[name].get('DOC_STORE_CONFIG', {}),
            settings.MODULESTORE[name].get('OPTIONS', {})
        )
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
        try:
            loc_cache = get_cache('loc_cache')
        except InvalidCacheBackendError:
            loc_cache = get_cache('default')
        # instantiate
        _loc_singleton = LocMapperStore(loc_cache, **settings.DOC_STORE_CONFIG)
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
    # pylint: disable=W0603
    global _loc_singleton
    cache = getattr(_loc_singleton, "cache", None)
    if cache:
        cache.clear()
    _loc_singleton = None


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
    if hasattr(store, 'create_course'):
        return store

    else:
        return None


class ModuleI18nService(object):
    """
    Implement the XBlock runtime "i18n" service.

    Mostly a pass-through to Django's translation module.
    django.utils.translation implements the gettext.Translations interface (it
    has ugettext, ungettext, etc), so we can use it directly as the runtime
    i18n service.

    """
    def __getattr__(self, name):
        return getattr(django.utils.translation, name)

    def strftime(self, *args, **kwargs):
        """
        A locale-aware implementation of strftime.
        """
        # This is the wrong place to import this function.  I'm putting it here
        # because the xmodule test suite can't import this module, because
        # Django is not available in that suite.  This function isn't called in
        # that suite, so this hides the import so the test won't fail.
        #
        # As I said, this is wrong.  But Cale says this code will soon be
        # refactored to a place that will be right, and the code can be made
        # right there.  If you are reading this comment after April 1, 2014,
        # then Cale was a liar.
        from util.date_utils import strftime_localized
        return strftime_localized(*args, **kwargs)
