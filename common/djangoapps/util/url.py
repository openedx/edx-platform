"""
Utility functions related to urls.
"""

import sys
from django.conf import settings
from django.core.urlresolvers import set_urlconf
from importlib import import_module


def reload_django_url_config():
    """
    Reloads Django's URL config.
    This is useful, for example, when a test enables new URLs
    with a django setting and the URL config needs to be refreshed.
    """
    urlconf = settings.ROOT_URLCONF
    if urlconf and urlconf in sys.modules:
        reload(sys.modules[urlconf])
    reloaded = import_module(urlconf)
    reloaded_urls = reloaded.urlpatterns
    set_urlconf(tuple(reloaded_urls))


def strip_port_from_host(host):
    """
    Strips port number from host
    """
    return host.split(':')[0]
