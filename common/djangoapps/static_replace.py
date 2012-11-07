import logging
import re

from staticfiles.storage import staticfiles_storage
from staticfiles import finders
from django.conf import settings

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.contentstore.content import StaticContent

log = logging.getLogger(__name__)

def try_staticfiles_lookup(path):
    """
    Try to lookup a path in staticfiles_storage.  If it fails, return
    a dead link instead of raising an exception.
    """
    try:
        url = staticfiles_storage.url(path)
    except Exception as err:
        log.warning("staticfiles_storage couldn't find path {0}: {1}".format(
            path, str(err)))
        # Just return the original path; don't kill everything.
        url = path
    return url


def replace(static_url, prefix=None, course_namespace=None):
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
        # cdodge: to support the change over to Mongo backed content stores, lets
        # use the utility functions in StaticContent.py
        if static_url.group('prefix') == '/static/' and not isinstance(modulestore(), XMLModuleStore):
            if course_namespace is None:
                raise BaseException('You must pass in course_namespace when remapping static content urls with MongoDB stores')
            url = StaticContent.convert_legacy_static_url(static_url.group('rest'), course_namespace)
        else:
            url = try_staticfiles_lookup(prefix + static_url.group('rest'))

        new_link = "".join([quote, url, quote])
        return new_link



def replace_urls(text, staticfiles_prefix=None, replace_prefix='/static/', course_namespace=None):
    def replace_url(static_url):
        return replace(static_url, staticfiles_prefix, course_namespace = course_namespace)

    return re.sub(r"""
        (?x)                 # flags=re.VERBOSE
        (?P<quote>\\?['"])   # the opening quotes
        (?P<prefix>{prefix}) # the prefix
        (?P<rest>.*?)        # everything else in the url
        (?P=quote)           # the first matching closing quote
        """.format(prefix=replace_prefix), replace_url, text)
