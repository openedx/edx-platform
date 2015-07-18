"""
This file implements the Microsite support for the Open edX platform.
A microsite enables the following features:

1) Mapping of sub-domain name to a 'brand', e.g. foo-university.edx.org
2) Present a landing page with a listing of courses that are specific to the 'brand'
3) Ability to swap out some branding elements in the website
"""
import inspect

from importlib import import_module
from django.conf import settings
from microsite_configuration.backends.base import BaseMicrositeBackend
CURRENT_REQUEST_CONFIGURATION.cache = {}


__all__ = [
    'is_request_in_microsite', 'get_value', 'has_override_value',
    'get_template_path', 'get_value_for_org', 'get_all_orgs',
    'clear', 'set_by_domain', 'enable_microsites',
]

BACKEND = None


def get_key_from_cache(key):
    """
    Retrieves a key from a cache scoped to the thread
    """
    if hasattr(CURRENT_REQUEST_CONFIGURATION, 'cache'):
        return CURRENT_REQUEST_CONFIGURATION.cache.get(key)


def set_key_to_cache(key, value):
    """
    Stores a key value pair in a cache scoped to the thread
    """
    if hasattr(CURRENT_REQUEST_CONFIGURATION, 'cache'):
        CURRENT_REQUEST_CONFIGURATION.cache[key] = value


def is_request_in_microsite():
    """
    This will return if current request is a request within a microsite
    """
    return BACKEND.is_request_in_microsite()


def get_value(val_name, default=None, **kwargs):
    """
    Returns a value associated with the request's microsite, if present
    """
    return BACKEND.get_value(val_name, default, **kwargs)


def get_dict(dict_name, default=None):
    """
    Returns a dictionary product of merging the request's microsite and
    the default value.
    This can be used, for example, to return a merged dictonary from the
    settings.FEATURES dict, including values defined at the microsite
    """
    cached_dict = get_key_from_cache(dict_name)
    if cached_dict:
        return cached_dict

    if default is None:
        default = {}

    output = default.copy()
    output.update(get_value(dict_name, {}))

    set_key_to_cache(dict_name, output)
    return output


def has_override_value(val_name):
    """
    Returns True/False whether a Microsite has a definition for the
    specified named value
    """
    return BACKEND.has_override_value(val_name)


def get_template_path(relative_path, **kwargs):
    """
    Returns a path (string) to a Mako template
    """
    return BACKEND.get_template_path(relative_path, **kwargs)


def get_value_for_org(org, val_name, default=None):
    """
    This returns a configuration value for a microsite which has an org_filter that matches
    what is passed in
    """
    return BACKEND.get_value_for_org(org, val_name, default)


def get_all_orgs():
    """
    This returns a set of orgs that are considered within a microsite. This can be used,
    for example, to do filtering
    """
    return BACKEND.get_all_orgs()


def clear():
    """
    Clears out any microsite configuration from the current request/thread
    """
    BACKEND.clear()
    CURRENT_REQUEST_CONFIGURATION.cache = {}


def set_by_domain(domain):
    """
    For a given request domain, find a match in our microsite configuration
    and make it available to the complete django request process
    """
    BACKEND.set_config_by_domain(domain)


def enable_microsites(log):
    """
    Enable the use of microsites during the startup script
    """
    BACKEND.enable_microsites(log)


def get_backend(backend_name=None, **kwds):
    """
    Load a microsites backend and return an instance of it.
    If backend is None (default) settings.MICROSITE_BACKEND is used.
    Any aditional args(kwds) will be used in the constructor of the backend.
    """
    name = backend_name or settings.MICROSITE_BACKEND
    try:
        parts = name.split('.')
        module_name = '.'.join(parts[:-1])
        class_name = parts[-1]
    except IndexError:
        raise ValueError('Invalid microsites backend %s' % name)

    try:
        module = import_module(module_name)
        cls = getattr(module, class_name)
        if not inspect.isclass(cls) or not issubclass(cls, BaseMicrositeBackend):
            raise TypeError
    except (AttributeError, ValueError):
        raise ValueError('Cannot find microsites backend %s' % module_name)

    return cls(**kwds)


BACKEND = get_backend()
