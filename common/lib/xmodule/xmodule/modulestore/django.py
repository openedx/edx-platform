"""
Module that provides a connection to the ModuleStore specified in the django settings.

Passes settings.MODULESTORE as kwargs to MongoModuleStore
"""

from __future__ import absolute_import

from importlib import import_module
from django.conf import settings
if not settings.configured:
    settings.configure()
from django.core.cache import get_cache, InvalidCacheBackendError
import django.utils

import re
import threading

from xmodule.util.django import get_current_request_hostname
import xmodule.modulestore  # pylint: disable=unused-import
from xmodule.contentstore.django import contentstore
import xblock.reference.plugins

# We may not always have the request_cache module available
try:
    from request_cache.middleware import RequestCache
    HAS_REQUEST_CACHE = True
except ImportError:
    HAS_REQUEST_CACHE = False

ASSET_IGNORE_REGEX = getattr(settings, "ASSET_IGNORE_REGEX", r"(^\._.*$)|(^\.DS_Store$)|(^.*~$)")


def load_function(path):
    """
    Load a function by name.

    path is a string of the form "path.to.module.function"
    returns the imported python object `function` from `path.to.module`
    """
    module_path, _, name = path.rpartition('.')
    return getattr(import_module(module_path), name)


def create_modulestore_instance(engine, content_store, doc_store_config, options, i18n_service=None, fs_service=None):
    """
    This will return a new instance of a modulestore given an engine and options
    """
    class_ = load_function(engine)

    _options = {}
    _options.update(options)

    FUNCTION_KEYS = ['render_template']
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
        contentstore=content_store,
        metadata_inheritance_cache_subsystem=metadata_inheritance_cache,
        request_cache=request_cache,
        xblock_mixins=getattr(settings, 'XBLOCK_MIXINS', ()),
        xblock_select=getattr(settings, 'XBLOCK_SELECT_FUNCTION', None),
        doc_store_config=doc_store_config,
        i18n_service=i18n_service or ModuleI18nService(),
        fs_service=fs_service or xblock.reference.plugins.FSService(),
        branch_setting_func=_get_modulestore_branch_setting,
        create_modulestore_instance=create_modulestore_instance,
        **_options
    )


# A singleton instance of the Mixed Modulestore
_MIXED_MODULESTORE = None


def modulestore():
    """
    Returns the Mixed modulestore
    """
    global _MIXED_MODULESTORE  # pylint: disable=global-statement
    if _MIXED_MODULESTORE is None:
        _MIXED_MODULESTORE = create_modulestore_instance(
            settings.MODULESTORE['default']['ENGINE'],
            contentstore(),
            settings.MODULESTORE['default'].get('DOC_STORE_CONFIG', {}),
            settings.MODULESTORE['default'].get('OPTIONS', {})
        )

    return _MIXED_MODULESTORE


def clear_existing_modulestores():
    """
    Clear the existing modulestore instances, causing
    them to be re-created when accessed again.

    This is useful for flushing state between unit tests.
    """
    global _MIXED_MODULESTORE  # pylint: disable=global-statement
    _MIXED_MODULESTORE = None


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


def _get_modulestore_branch_setting():
    """
    Returns the branch setting for the module store from the current Django request if configured,
    else returns the branch value from the configuration settings if set,
    else returns None

    The value of the branch setting is cached in a thread-local variable so it is not repeatedly recomputed
    """
    def get_branch_setting():
        """
        Finds and returns the branch setting based on the Django request and the configuration settings
        """
        branch = None
        hostname = get_current_request_hostname()
        if hostname:
            # get mapping information which is defined in configurations
            mappings = getattr(settings, 'HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS', None)

            # compare hostname against the regex expressions set of mappings which will tell us which branch to use
            if mappings:
                for key in mappings.iterkeys():
                    if re.match(key, hostname):
                        return mappings[key]
        if branch is None:
            branch = getattr(settings, 'MODULESTORE_BRANCH', None)
        return branch

    # leaving this in code structured in closure-friendly format b/c we might eventually cache this (again)
    # using request_cache
    return get_branch_setting()
