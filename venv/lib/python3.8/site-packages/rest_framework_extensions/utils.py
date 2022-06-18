import itertools
from distutils.version import LooseVersion

import rest_framework

from rest_framework_extensions.key_constructor.constructors import (
    DefaultKeyConstructor,
    DefaultObjectKeyConstructor,
    DefaultListKeyConstructor,
    DefaultAPIModelInstanceKeyConstructor,
    DefaultAPIModelListKeyConstructor
)
from rest_framework_extensions.settings import extensions_api_settings


def get_rest_framework_version():
    return tuple(LooseVersion(rest_framework.VERSION).version)


def flatten(list_of_lists):
    """
    Takes an iterable of iterables,
    returns a single iterable containing all items
    """
    # todo: test me
    return itertools.chain(*list_of_lists)


def prepare_header_name(name):
    """
    >> prepare_header_name('Accept-Language')
    http_accept_language
    """
    return 'http_{0}'.format(name.strip().replace('-', '_')).upper()


def get_unique_method_id(view_instance, view_method):
    # todo: test me as UniqueMethodIdKeyBit
    return '.'.join([
        view_instance.__module__,
        view_instance.__class__.__name__,
        view_method.__name__
    ])


def get_model_opts_concrete_fields(opts):
    # todo: test me
    if not hasattr(opts, 'concrete_fields'):
        opts.concrete_fields = [f for f in opts.fields if f.column is not None]
    return opts.concrete_fields


def compose_parent_pk_kwarg_name(value):
    return '{0}{1}'.format(
        extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX,
        value
    )


default_cache_key_func = DefaultKeyConstructor()
default_object_cache_key_func = DefaultObjectKeyConstructor()
default_list_cache_key_func = DefaultListKeyConstructor()

default_etag_func = default_cache_key_func
default_object_etag_func = default_object_cache_key_func
default_list_etag_func = default_list_cache_key_func

# API (object-centered) functions
default_api_object_etag_func = DefaultAPIModelInstanceKeyConstructor()
default_api_list_etag_func = DefaultAPIModelListKeyConstructor()
