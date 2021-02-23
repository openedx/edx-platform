"""
Tests for content rendering
"""


from unittest import TestCase

import ddt

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
        assert render_body('{delimiter}some text{delimiter}'.format(delimiter=delimiter)) == \
               '<p><{tag}>some text</{tag}></p>'.format(tag=tag)

    @ddt.data(
        "b", "blockquote", "code", "del", "dd", "dl", "dt", "em", "h1", "h2", "h3", "i", "kbd",
        "li", "ol", "p", "pre", "s", "sup", "sub", "strong", "strike", "ul"
    )
    def test_openclose_tag(self, tag):
        raw_body = "<{tag}>some text</{tag}>".format(tag=tag)
        is_inline_tag = tag in ["b", "code", "del", "em", "i", "kbd", "s", "sup", "sub", "strong", "strike"]
        rendered_body = _add_p_tags(raw_body) if is_inline_tag else raw_body
        assert render_body(raw_body) == rendered_body

    @ddt.data("br", "hr")
    def test_selfclosing_tag(self, tag):
        raw_body = f"<{tag}>"
        is_inline_tag = tag == "br"
        rendered_body = _add_p_tags(raw_body) if is_inline_tag else raw_body
        assert render_body(raw_body) == rendered_body

    @ddt.data("http", "https", "ftp")
    def test_allowed_a_tag(self, protocol):
        raw_body = f'<a href="{protocol}://foo" title="bar">baz</a>'
        assert render_body(raw_body) == _add_p_tags(raw_body)

    def test_disallowed_a_tag(self):
        raw_body = '<a href="gopher://foo">link content</a>'
        assert render_body(raw_body) == '<p>link content</p>'

    @ddt.data("http", "https")
    def test_allowed_img_tag(self, protocol):
        raw_body = '<img src="{protocol}://foo" width="111" height="222" alt="bar" title="baz">'.format(
            protocol=protocol
        )
        assert render_body(raw_body) == _add_p_tags(raw_body)

    def test_disallowed_img_tag(self):
        raw_body = '<img src="gopher://foo">'
        assert render_body(raw_body) == '<p></p>'

    def test_script_tag(self):
        raw_body = '<script type="text/javascript">alert("evil script");</script>'
        assert render_body(raw_body) == 'alert("evil script");'

    @ddt.data("p", "br", "li", "hr")  # img is tested above
    def test_allowed_unpaired_tags(self, tag):
        raw_body = f"foo<{tag}>bar"
        assert render_body(raw_body) == _add_p_tags(raw_body)

    def test_unpaired_start_tag(self):
        assert render_body('foo<i>bar') == '<p>foobar</p>'

    def test_unpaired_end_tag(self):
        assert render_body('foo</i>bar') == '<p>foobar</p>'

    def test_interleaved_tags(self):
        assert render_body('foo<i>bar<b>baz</i>quux</b>greg') == '<p>foo<i>barbaz</i>quuxgreg</p>'
