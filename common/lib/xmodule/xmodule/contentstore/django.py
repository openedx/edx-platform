from __future__ import absolute_import
from importlib import import_module


from django.conf import settings
from cache_toolbox.core import del_cached_content

_CONTENTSTORE = {}


def load_function(path):
    """
    Load a function by name.

    path is a string of the form "path.to.module.function"
    returns the imported python object `function` from `path.to.module`
    """
    module_path, _, name = path.rpartition('.')
    return getattr(import_module(module_path), name)


def contentstore(name='default', delete_from_toolbox_cache=False):
    if name not in _CONTENTSTORE:
        class_ = load_function(settings.CONTENTSTORE['ENGINE'])
        options = {}
        options.update(settings.CONTENTSTORE['DOC_STORE_CONFIG'])

        if delete_from_toolbox_cache == True:
            options.update({'delete_from_cache': del_cached_content})

        if 'ADDITIONAL_OPTIONS' in settings.CONTENTSTORE:
            if name in settings.CONTENTSTORE['ADDITIONAL_OPTIONS']:
                options.update(settings.CONTENTSTORE['ADDITIONAL_OPTIONS'][name])
        _CONTENTSTORE[name] = class_(**options)

    return _CONTENTSTORE[name]
