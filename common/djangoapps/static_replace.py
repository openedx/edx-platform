from staticfiles.storage import staticfiles_storage
from staticfiles import finders
from django.conf import settings
import re


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
        url = staticfiles_storage.url(prefix + static_url.group('rest'))
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
