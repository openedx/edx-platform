"""
Module implementing `xblock.runtime.Runtime` functionality for the LMS
"""

import re

from django.core.urlresolvers import reverse

from xmodule.x_module import ModuleSystem


def _quote_slashes(match):
    """
    Helper function for `quote_slashes`
    """
    matched = match.group(0)
    # We have to escape ';', because that is our
    # escape sequence identifier (otherwise, the escaping)
    # couldn't distinguish between us adding ';_' to the string
    # and ';_' appearing naturally in the string
    if matched == ';':
        return ';;'
    elif matched == '/':
        return ';_'
    else:
        return matched


def quote_slashes(text):
    """
    Quote '/' characters so that they aren't visible to
    django's url quoting, unquoting, or url regex matching.

    Escapes '/'' to the sequence ';_', and ';' to the sequence
    ';;'. By making the escape sequence fixed length, and escaping
    identifier character ';', we are able to reverse the escaping.
    """
    return re.sub(ur'[;/]', _quote_slashes, text)


def _unquote_slashes(match):
    """
    Helper function for `unquote_slashes`
    """
    matched = match.group(0)
    if matched == ';;':
        return ';'
    elif matched == ';_':
        return '/'
    else:
        return matched


def unquote_slashes(text):
    """
    Unquote slashes quoted by `quote_slashes`
    """
    return re.sub(r'(;;|;_)', _unquote_slashes, text)


class LmsHandlerUrls(object):
    """
    A runtime mixin that provides a handler_url function that routes
    to the LMS' xblock handler view.

    This must be mixed in to a runtime that already accepts and stores
    a course_id
    """
    # pylint: disable=unused-argument
    # pylint: disable=no-member
    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        """See :method:`xblock.runtime:Runtime.handler_url`"""
        view_name = 'xblock_handler'
        if handler_name:
            # Be sure this is really a handler.
            func = getattr(block, handler_name, None)
            if not func:
                raise ValueError("{!r} is not a function name".format(handler_name))
            if not getattr(func, "_is_xblock_handler", False):
                raise ValueError("{!r} is not a handler name".format(handler_name))

        if thirdparty:
            view_name = 'xblock_handler_noauth'

        url = reverse(view_name, kwargs={
            'course_id': self.course_id,
            'usage_id': quote_slashes(unicode(block.scope_ids.usage_id).encode('utf-8')),
            'handler': handler_name,
            'suffix': suffix,
        })

        # If suffix is an empty string, remove the trailing '/'
        if not suffix:
            url = url.rstrip('/')

        # If there is a query string, append it
        if query:
            url += '?' + query

        return url


class LmsModuleSystem(LmsHandlerUrls, ModuleSystem):  # pylint: disable=abstract-method
    """
    ModuleSystem specialized to the LMS
    """
    pass
