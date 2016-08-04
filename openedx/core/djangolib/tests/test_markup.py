# -*- coding: utf-8 -*-
"""
Tests for openedx.core.djangolib.markup
"""

from nose.plugins.attrib import attr
import unittest

import ddt
from django.utils.translation import ugettext as _, ungettext
from mako.template import Template

from openedx.core.djangolib.markup import HTML, Text


@attr(shard=2)
@ddt.ddt
class FormatHtmlTest(unittest.TestCase):
    """Test that we can format plain strings and HTML into them properly."""

    @ddt.data(
        (u"hello", u"hello"),
        (u"<hello>", u"&lt;hello&gt;"),
        (u"It's cool", u"It&#39;s cool"),
        (u'"cool," she said.', u'&#34;cool,&#34; she said.'),
        (u"Stop & Shop", u"Stop &amp; Shop"),
        (u"<a>нтмℓ-єѕ¢αρє∂</a>", u"&lt;a&gt;нтмℓ-єѕ¢αρє∂&lt;/a&gt;"),
    )
    def test_simple(self, (before, after)):
        self.assertEqual(unicode(Text(_(before))), after)  # pylint: disable=translation-of-non-string
        self.assertEqual(unicode(Text(before)), after)

    def test_formatting(self):
        # The whole point of this function is to make sure this works:
        out = Text(_(u"Point & click {start}here{end}!")).format(
            start=HTML("<a href='http://edx.org'>"),
            end=HTML("</a>"),
        )
        self.assertEqual(
            unicode(out),
            u"Point &amp; click <a href='http://edx.org'>here</a>!",
        )

    def test_nested_formatting(self):
        # Sometimes, you have plain text, with html inserted, and the html has
        # plain text inserted.  It gets twisty...
        out = Text(_(u"Send {start}email{end}")).format(
            start=HTML("<a href='mailto:{email}'>").format(email="A&B"),
            end=HTML("</a>"),
        )
        self.assertEqual(
            unicode(out),
            u"Send <a href='mailto:A&amp;B'>email</a>",
        )

    def test_mako(self):
        # The default_filters used here have to match the ones in edxmako.
        template = Template(
            """
                <%!
                from django.utils.translation import ugettext as _

                from openedx.core.djangolib.markup import HTML, Text
                %>
                ${Text(_(u"A & {BC}")).format(BC=HTML("B & C"))}
            """,
            default_filters=['decode.utf8', 'h'],
        )
        out = template.render()
        self.assertEqual(out.strip(), u"A &amp; B & C")

    def test_ungettext(self):
        for i in [1, 2]:
            out = Text(ungettext("1 & {}", "2 & {}", i)).format(HTML("<>"))
            self.assertEqual(out, "{} &amp; <>".format(i))
