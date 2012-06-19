from staticfiles.storage import staticfiles_storage
import re

PREFIX = '/static/'
STATIC_PATTERN = re.compile(r"""
(?P<quote>['"])  # the opening quotes
{prefix}         # the prefix
(?P<rest>.*?)    # everything else in the url
(?P=quote)       # the first matching closing quote
""".format(prefix=PREFIX), re.VERBOSE)
PREFIX_LEN = len(PREFIX)

def replace(static_url):
    quote = static_url.group('quote')
    url = staticfiles_storage.url(static_url.group('rest'))
    return "".join([quote, url, quote])

def replace_urls(text):
    return STATIC_PATTERN.sub(replace, text)
