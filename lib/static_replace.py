from staticfiles.storage import staticfiles_storage
import re

PREFIX = '/static/'
STATIC_PATTERN = re.compile(r"""
(?P<quote>['"])  # the opening quotes
{prefix}         # the prefix
.*?              # everything else in the url
(?P=quote)       # the first matching closing quote
""".format(prefix=PREFIX), re.VERBOSE)
PREFIX_LEN = len(PREFIX)

def replace(static_url):
    quote = static_url[0]
    url = staticfiles_storage.url(static_url[1+PREFIX_LEN:-1])
    return "".join([quote, url, quote])

def replace_urls(text):
    return STATIC_PATTERN.sub(replace, text)
