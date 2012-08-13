import logging
import re

from staticfiles.storage import staticfiles_storage
from staticfiles import finders
from django.conf import settings

log = logging.getLogger(__name__)

def try_staticfiles_lookup(path):
    """
    Try to lookup a path in staticfiles_storage.  If it fails, return
    a dead link instead of raising an exception.
    """
    try:
        url = staticfiles_storage.url(path)
    except Exception as err:
        log.warning("staticfiles_storage couldn't find path {}: {}".format(
            path, str(err)))
        # Just return a dead link--don't kill everything.
        url = "file_not_found"
    return url


def replace(static_url, prefix=None):
    if prefix is None:
        prefix = ''
    else:
        prefix = prefix + '/'

    quote = static_url.group('quote')

    servable = (
        # If in debug mode, we'll serve up anything that the finders can find
        (settings.DEBUG and finders.find(static_url.group('rest'), True)) or
        # Otherwise, we'll only serve up stuff that the storages can find
        staticfiles_storage.exists(static_url.group('rest'))
    )

    if servable:
        return static_url.group(0)
    else:
        # don't error if file can't be found
        url = try_staticfiles_lookup(prefix + static_url.group('rest'))
        return "".join([quote, url, quote])


def replace_urls(text, staticfiles_prefix=None, replace_prefix='/static/'):
    def replace_url(static_url):
        return replace(static_url, staticfiles_prefix)

    return re.sub(r"""
        (?x)                 # flags=re.VERBOSE
        (?P<quote>\\?['"])   # the opening quotes
        (?P<prefix>{prefix}) # the prefix
        (?P<rest>.*?)        # everything else in the url
        (?P=quote)           # the first matching closing quote
        """.format(prefix=replace_prefix), replace_url, text)
