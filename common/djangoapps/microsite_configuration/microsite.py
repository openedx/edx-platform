"""
This file implements the Microsite support for the Open edX platform.
A microsite enables the following features:

1) Mapping of sub-domain name to a 'brand', e.g. foo-university.edx.org
2) Present a landing page with a listing of courses that are specific to the 'brand'
3) Ability to swap out some branding elements in the website
"""
import threading
import os.path

from django.conf import settings

CURRENT_REQUEST_CONFIGURATION = threading.local()
CURRENT_REQUEST_CONFIGURATION.data = {}


def has_configuration_set():
    """
    Returns whether there is any Microsite configuration settings
    """
    return getattr(settings, "MICROSITE_CONFIGURATION", False)


def get_configuration():
    """
    Returns the current request's microsite configuration
    """
    if not hasattr(CURRENT_REQUEST_CONFIGURATION, 'data'):
        return {}

    return CURRENT_REQUEST_CONFIGURATION.data


def is_request_in_microsite():
    """
    This will return if current request is a request within a microsite
    """
    return bool(get_configuration())


def get_value(val_name, default=None):
    """
    Returns a value associated with the request's microsite, if present
    """
    configuration = get_configuration()
    return configuration.get(val_name, default)


def get_template_path(relative_path):
    """
    Returns a path (string) to a Mako template, which can either be in
    a microsite directory (as an override) or will just return what is passed in which is
    expected to be a string
    """

    if not is_request_in_microsite():
        return relative_path

    microsite_template_path = str(get_value('template_dir'))

    if microsite_template_path:
        search_path = os.path.join(microsite_template_path, relative_path)

        if os.path.isfile(search_path):
            path = '{0}/templates/{1}'.format(
                get_value('microsite_name'),
                relative_path
            )
            return path

    return relative_path


def get_value_for_org(org, val_name, default=None):
    """
    This returns a configuration value for a microsite which has an org_filter that matches
    what is passed in
    """
    if not has_configuration_set():
        return default

    for value in settings.MICROSITE_CONFIGURATION.values():
        org_filter = value.get('course_org_filter', None)
        if org_filter == org:
            return value.get(val_name, default)
    return default


def get_all_orgs():
    """
    This returns a set of orgs that are considered within a microsite. This can be used,
    for example, to do filtering
    """
    org_filter_set = set()
    if not has_configuration_set():
        return org_filter_set

    for value in settings.MICROSITE_CONFIGURATION.values():
        org_filter = value.get('course_org_filter')
        if org_filter:
            org_filter_set.add(org_filter)

    return org_filter_set


def clear():
    """
    Clears out any microsite configuration from the current request/thread
    """
    CURRENT_REQUEST_CONFIGURATION.data = {}


def _set_current_microsite(microsite_config_key, subdomain, domain):
    """
    Helper internal method to actually put a microsite on the threadlocal
    """
    config = settings.MICROSITE_CONFIGURATION[microsite_config_key].copy()
    config['subdomain'] = subdomain
    config['site_domain'] = domain
    CURRENT_REQUEST_CONFIGURATION.data = config


def set_by_domain(domain):
    """
    For a given request domain, find a match in our microsite configuration and then assign
    it to the thread local so that it is available throughout the entire
    Django request processing
    """
    if not has_configuration_set() or not domain:
        return

    for key, value in settings.MICROSITE_CONFIGURATION.items():
        subdomain = value.get('domain_prefix')
        if subdomain and domain.startswith(subdomain):
            _set_current_microsite(key, subdomain, domain)
            return

    # if no match on subdomain then see if there is a 'default' microsite defined
    # if so, then use that
    if 'default' in settings.MICROSITE_CONFIGURATION:
        _set_current_microsite('default', subdomain, domain)
