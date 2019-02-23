# -*- coding: utf-8 -*-
"""
Tests for openedx.core.djangolib.markup
"""

import unittest

import ddt
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from mako.template import Template

from openedx.core.djangolib.markup import HTML, Text, strip_all_tags_but_br


@ddt.ddt
class FormatHtmlTest(unittest.TestCase):
    """Test that we can format plain strings and HTML into them properly."""

    @ddt.data(
        ("hello", "hello"),
        ("<hello>", "&lt;hello&gt;"),
        ("It's cool", "It&#39;s cool"),
        ('"cool," she said.', '&#34;cool,&#34; she said.'),
        ("Stop & Shop", "Stop &amp; Shop"),
        ("<a>нтмℓ-єѕ¢αρє∂</a>", "&lt;a&gt;нтмℓ-єѕ¢αρє∂&lt;/a&gt;"),
    )
    def test_simple(self, before_after):
        (before, after) = before_after
        self.assertEqual(str(Text(_(before))), after)
        self.assertEqual(str(Text(before)), after)

    def test_formatting(self):
        # The whole point of this function is to make sure this works:
        out = Text(_("Point & click {start}here{end}!")).format(
            start=HTML("<a href='http://edx.org'>"),
            end=HTML("</a>"),
        )
        self.assertEqual(
            str(out),
            "Point &amp; click <a href='http://edx.org'>here</a>!",
        )

    def test_nested_formatting(self):
        # Sometimes, you have plain text, with html inserted, and the html has
        # plain text inserted.  It gets twisty...
        out = Text(_("Send {start}email{end}")).format(
            start=HTML("<a href='mailto:{email}'>").format(email="A&B"),
            end=HTML("</a>"),
        )
        self.assertEqual(
            str(out),
            "Send <a href='mailto:A&amp;B'>email</a>",
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
        self.assertEqual(out.strip(), "A &amp; B & C")

    def test_ungettext(self):
        for i in [1, 2]:
            out = Text(ungettext("1 & {}", "2 & {}", i)).format(HTML("<>"))
            self.assertEqual(out, "{} &amp; <>".format(i))

    def test_strip_all_tags_but_br_filter(self):
        """ Verify filter removes every tags except br """
        template = Template(
            """
                <%page expression_filter="h"/>
                <%!
                from openedx.core.djangolib.markup import strip_all_tags_but_br
                %>
                ${" course <br> title <script>" | n, strip_all_tags_but_br}
            """
        )
        rendered_template = template.render()

        self.assertIn('<br>', rendered_template)
        self.assertNotIn('<script>', rendered_template)

    def test_strip_all_tags_but_br_returns_html(self):
        """
        Verify filter returns HTML Markup safe string object
        """

        html = strip_all_tags_but_br('{name}<br><script>')
        html = html.format(name='Rock & Roll')
        self.assertEqual(html.decode(), 'Rock &amp; Roll<br>')
