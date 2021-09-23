"""
Tests for content rendering
"""


import ddt
from django.test import TestCase

from lms.djangoapps.discussion.rest_api.render import render_body


def _add_p_tags(raw_body):
    """Return raw_body surrounded by p tags"""
    return f"<p>{raw_body}</p>"


@ddt.ddt
class RenderBodyTest(TestCase):
    """Tests for render_body"""

    def test_empty(self):
        assert render_body('') == ''

    @ddt.data(
        ("*", "em"),
        ("**", "strong"),
        ("`", "code"),
    )
    @ddt.unpack
    def test_markdown_inline(self, delimiter, tag):
        assert render_body(f'{delimiter}some text{delimiter}') == f'<p><{tag}>some text</{tag}></p>'

    @ddt.data(
        "b", "blockquote", "code", "del", "dd", "dl", "dt", "em", "h1", "h2", "h3", "i", "kbd",
        "li", "ol", "p", "pre", "s", "sup", "sub", "strong", "strike", "ul"
    )
    def test_openclose_tag(self, tag):
        raw_body = f"<{tag}>some text</{tag}>"
        is_inline_tag = tag in ["b", "code", "del", "em", "i", "kbd", "s", "sup", "sub", "strong", "strike"]
        rendered_body = _add_p_tags(raw_body) if is_inline_tag else raw_body
        assert render_body(raw_body) == rendered_body

    @ddt.data("br", "hr")
    def test_selfclosing_tag(self, tag):
        raw_body = f"<{tag}>"
        is_inline_tag = tag == "br"
        rendered_body = _add_p_tags(raw_body) if is_inline_tag else raw_body
        assert render_body(raw_body) == rendered_body

    @ddt.data(
        ("http", True),
        ("https", True),
        ("ftp", True),
        ("gopher", False),
        ("file", False),
        ("data", False),
    )
    @ddt.unpack
    def test_protocols_a_tag(self, protocol, is_allowed):
        raw_body = f'<a href="{protocol}://foo" title="bar">baz</a>'
        cleaned_body = '<a title="bar">baz</a>'
        rendered = render_body(raw_body)
        if is_allowed:
            assert rendered == _add_p_tags(raw_body)
        else:
            assert rendered == _add_p_tags(cleaned_body)

    @ddt.data(
        ("http", True),
        ("https", True),
        ("gopher", False),
        ("file", False),
        ("data", False),
    )
    @ddt.unpack
    def test_protocols_img_tag(self, protocol, is_allowed):
        raw_body = f'<img alt="bar" height="222" src="{protocol}://foo" title="baz" width="111">'
        cleaned_body = '<img alt="bar" height="222" title="baz" width="111">'
        rendered = render_body(raw_body)
        if is_allowed:
            assert rendered == _add_p_tags(raw_body)
        else:
            assert rendered == _add_p_tags(cleaned_body)

    def test_script_tag(self):
        raw_body = '<script type="text/javascript">alert("evil script");</script>'
        assert render_body(raw_body) == 'alert("evil script");'

    @ddt.data(
        ("br", '<p>foo<br>bar</p>'),  # br is allowed inside p
        ("li", '<p>foo</p><li>bar<p></p></li>'),  # unpaired li only allowed if followed by another li
        ("hr", '<p>foo</p><hr>bar<p></p>'),  # hr is not allowed inside p
        ("img", '<p>foo<img>bar</p>'),  # unpaired img allowed, empty img doesn't render
        ("i", '<p>foo<i>bar</i></p>'),
    )
    @ddt.unpack
    def test_unpaired_tags(self, tag, rendered_output):
        raw_body = f"foo<{tag}>bar"
        assert render_body(raw_body) == rendered_output

    def test_interleaved_tags(self):
        self.assertHTMLEqual(
            render_body('foo<i>bar<b>baz</i>quux</b>greg'),
            '<p>foo<i>bar<b>baz</b></i><b>quux</b>greg</p>',
        )
