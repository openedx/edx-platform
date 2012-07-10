from staticfiles.storage import staticfiles_storage
import re


def replace(static_url, prefix=None):
    if prefix is None:
        prefix = ''
    else:
        prefix = prefix + '/'

    quote = static_url.group('quote')
    url = staticfiles_storage.url(prefix + static_url.group('rest'))
    return "".join([quote, url, quote])


def replace_urls(text, staticfiles_prefix=None, replace_prefix='/static/'):
    def replace_url(static_url):
        return replace(static_url, staticfiles_prefix)

    return re.sub(r"""
        (?P<quote>\\?['"])  # the opening quotes
        {prefix}         # the prefix
        (?P<rest>.*?)    # everything else in the url
        (?P=quote)       # the first matching closing quote
        """.format(prefix=replace_prefix), replace_url, text, flags=re.VERBOSE)
