"""
Utilities for use in Mako markup.
"""

from django.utils.translation import ugettext as django_ugettext
from django.utils.translation import ungettext as django_ungettext
import markupsafe


# So that we can use escape() imported from here.
escape = markupsafe.escape                      # pylint: disable=invalid-name


def ugettext(text):
    """Translate a string, and escape it as plain text.

    Use like this in Mako::

        <% from openedx.core.djangolib.markup import ugettext as _ %>
        <p>${_("Hello, world!")}</p>

    Or with formatting::

        <% from openedx.core.djangolib.markup import HTML, ugettext as _ %>
        ${_("Write & send {start}email{end}").format(
            start=HTML("<a href='mailto:ned@edx.org'>"),
            end=HTML("</a>"),
           )}

    """
    return markupsafe.escape(django_ugettext(text))


def ungettext(text1, text2, num):
    """Translate a number-sensitive string, and escape it as plain text."""
    return markupsafe.escape(django_ungettext(text1, text2, num))


def HTML(html):                                 # pylint: disable=invalid-name
    """Mark a string as already HTML, so that it won't be escaped before output.

    Use this when formatting HTML into other strings::

        <% from openedx.core.djangolib.markup import HTML, ugettext as _ %>
        ${_("Write & send {start}email{end}").format(
            start=HTML("<a href='mailto:ned@edx.org'>"),
            end=HTML("</a>"),
           )}

    """
    return markupsafe.Markup(html)
