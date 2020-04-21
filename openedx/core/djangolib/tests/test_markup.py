# -*- coding: utf-8 -*-
"""
Tests for openedx.core.djangolib.markup
"""


import unittest

import ddt
import six
from bs4 import BeautifulSoup
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from mako.template import Template

from openedx.core.djangolib.markup import HTML, Text, strip_all_tags_but_br


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
    def test_simple(self, before_after):
        (before, after) = before_after
        self.assertEqual(six.text_type(Text(_(before))), after)  # pylint: disable=translation-of-non-string
        self.assertEqual(six.text_type(Text(before)), after)

    def test_formatting(self):
        # The whole point of this function is to make sure this works:
        out = Text(_(u"Point & click {start}here{end}!")).format(
            start=HTML("<a href='http://edx.org'>"),
            end=HTML("</a>"),
        )
        self.assertEqual(
            six.text_type(out),
            u"Point &amp; click <a href='http://edx.org'>here</a>!",
        )

    def test_nested_formatting(self):
        # Sometimes, you have plain text, with html inserted, and the html has
        # plain text inserted.  It gets twisty...
        out = Text(_(u"Send {start}email{end}")).format(
            start=HTML(u"<a href='mailto:{email}'>").format(email="A&B"),
            end=HTML("</a>"),
        )
        self.assertEqual(
            six.text_type(out),
            u"Send <a href='mailto:A&amp;B'>email</a>",
        )

    def test_mako(self):
        # The default_filters used here have to match the ones in edxmako.
        template = Template(
            u"""
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
            out = Text(ungettext(u"1 & {}", u"2 & {}", i)).format(HTML(u"<>"))
            self.assertEqual(out, u"{} &amp; <>".format(i))

    def test_strip_all_tags_but_br_filter(self):
        """ Verify filter removes every tags except br """
        template = Template(
            u"""
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
        self.assertEqual(six.text_type(html), u'Rock &amp; Roll<br>')

    def test_clean_dengers_html_filter(self):
        """ Verify filter removes expected tags """
        template = Template(
            u"""
                <%page expression_filter="h"/>
                <%!
                from openedx.core.djangolib.markup import clean_dangerous_html
                %>
                <%
                    html_content = '''
                        <html>
                            <head>
                                <script type="text/javascript" src="evil-site"></script>
                                <link rel="alternate" type="text/rss" src="evil-rss">
                                <style>
                                    body {
                                        background-image: url(javascript:do_evil)
                                    };
                                    div {
                                        color: expression(evil)
                                    };
                                </style>
                            </head>
                            <body onload="evil_function()">
                                <!-- I am interpreted for EVIL! -->
                                <a href="javascript:evil_function()">a link</a>
                                <a href="#" onclick="evil_function()">another link</a>
                                <p onclick="evil_function()">a paragraph</p>
                                <div style="display: none">secret EVIL!</div>
                                <object> of EVIL!</object>
                                <iframe src="evil-site"></iframe>
                                <form action="evil-site">
                                    Password: <input type="password" name="password">
                                </form>
                                <blink>annoying EVIL!</blink>
                                <a href="evil-site">spam spam SPAM!</a>
                                <image src="evil!">
                            </body>
                        </html>
                    '''
                %>
                ${html_content | n, clean_dangerous_html}
            """
        )
        rendered_template = template.render()
        html_soup = BeautifulSoup(rendered_template, 'html.parser')

        self.assertTrue(html_soup.find('a'))
        self.assertTrue(html_soup.find('div'))
        self.assertTrue(html_soup.find('div', attrs={'style': 'display: none'}))
        self.assertTrue(html_soup.find('p'))
        self.assertTrue(html_soup.find('img'))

        self.assertFalse(html_soup.find('a', attrs={'onclick': 'evil_function()'}))
        self.assertFalse(html_soup.find('html'))
        self.assertFalse(html_soup.find('head'))
        self.assertFalse(html_soup.find('script'))
        self.assertFalse(html_soup.find('style'))
        self.assertFalse(html_soup.find('link'))
        self.assertFalse(html_soup.find('iframe'))
        self.assertFalse(html_soup.find('form'))
        self.assertFalse(html_soup.find('blink'))
        self.assertFalse(html_soup.find('object'))
