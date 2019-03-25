"""
Utilities for use in Mako markup.
"""

import markupsafe
import bleach
from mako.filters import decode

# Text() can be used to declare a string as plain text, as HTML() is used
# for HTML.  It simply wraps markupsafe's escape, which will HTML-escape if
# it isn't already escaped.
Text = markupsafe.escape                        # pylint: disable=invalid-name


def HTML(html):                                 # pylint: disable=invalid-name
    """
    Mark a string as already HTML, so that it won't be escaped before output.

    Use this function when formatting HTML into other strings.  It must be
    used in conjunction with ``Text()``, and both ``HTML()`` and ``Text()``
    must be closed before any calls to ``format()``::

        <%page expression_filter="h"/>
        <%!
        from django.utils.translation import ugettext as _

        from openedx.core.djangolib.markup import HTML, Text
        %>
        ${Text(_("Write & send {start}email{end}")).format(
            start=HTML("<a href='mailto:{}'>").format(user.email),
            end=HTML("</a>"),
        )}

    """
    return markupsafe.Markup(html)


def strip_all_tags_but_br(string_to_strip):
    """
    Strips all tags from a string except <br/> and marks as HTML.

    Usage:
        <%page expression_filter="h"/>
        <%!
        from openedx.core.djangolib.markup import strip_all_tags_but_br
        %>
        ${accomplishment_course_title | n, strip_all_tags_but_br}
    """

    if string_to_strip is None:
        string_to_strip = ""

    string_to_strip = decode.utf8(string_to_strip)
    string_to_strip = bleach.clean(string_to_strip, tags=['br'], strip=True)

    return HTML(string_to_strip)
