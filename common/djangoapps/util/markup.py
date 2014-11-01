"""
Utilities for use in Mako markup.
"""

from django.utils.translation import ugettext as django_ugettext
import markupsafe


def ugettext(text):
    """Translate a string, and escape it as plain text.

    Use like this in Mako::

        <% from util.markup import ugettext as _ %>
        <p>${_("Hello, world!")}</p>

    Or with formatting::

        <% from util.markup import HTML, ugettext as _ %>
        ${_("Write & send {start}email{end}").format(
                start=HTML("<a href='mailto:ned@edx.org'>"),
                end=HTML("</a>"),
                )}

    """
    return markupsafe.escape(django_ugettext(text))


def HTML(html):                                 # pylint: disable=invalid-name
    """Mark a string as already HTML, so that it won't be escaped before output.

    Use this when formatting HTML into other strings::

        <% from util.markup import HTML, ugettext as _ %>
        ${_("Write & send {start}email{end}").format(
                start=HTML("<a href='mailto:ned@edx.org'>"),
                end=HTML("</a>"),
                )}

    """
    return markupsafe.Markup(html)
