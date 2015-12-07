"""
Tests for js_utils.py
"""
import json
from unittest import TestCase
from openedx.core.lib.js_utils import (
    escape_json_dumps, escape_js_string
)


class TestJSUtils(TestCase):
    """
    Test JS utils
    """

    class NoDefaultEncoding(object):
        """
        Helper class that has no default JSON encoding
        """
        def __init__(self, value):
            self.value = value

    class SampleJSONEncoder(json.JSONEncoder):
        """
        A test encoder that is used to prove that the encoder does its job before the escaping.
        """
        # pylint: disable=method-hidden
        def default(self, noDefaultEncodingObj):
            return noDefaultEncodingObj.value.replace("<script>", "sample-encoder-was-here")

    def test_escape_json_dumps_escapes_unsafe_html(self):
        """
        Test escape_json_dumps properly escapes &, <, and >.
        """
        malicious_json = {"</script><script>alert('hello, ');</script>": "</script><script>alert('&world!');</script>"}
        expected_encoded_json = (
            r'''{"\u003c/script\u003e\u003cscript\u003ealert('hello, ');\u003c/script\u003e": '''
            r'''"\u003c/script\u003e\u003cscript\u003ealert('\u0026world!');\u003c/script\u003e"}'''
        )

        encoded_json = escape_json_dumps(malicious_json)
        self.assertEquals(expected_encoded_json, encoded_json)

    def test_escape_json_dumps_with_custom_encoder_escapes_unsafe_html(self):
        """
        Test escape_json_dumps first encodes with custom JSNOEncoder before escaping &, <, and >

        The test encoder class should first perform the replacement of "<script>" with
        "sample-encoder-was-here", and then should escape the remaining &, <, and >.

        """
        malicious_json = {
            "</script><script>alert('hello, ');</script>":
            self.NoDefaultEncoding("</script><script>alert('&world!');</script>")
        }
        expected_custom_encoded_json = (
            r'''{"\u003c/script\u003e\u003cscript\u003ealert('hello, ');\u003c/script\u003e": '''
            r'''"\u003c/script\u003esample-encoder-was-herealert('\u0026world!');\u003c/script\u003e"}'''
        )

        encoded_json = escape_json_dumps(malicious_json, cls=self.SampleJSONEncoder)
        self.assertEquals(expected_custom_encoded_json, encoded_json)

    def test_escape_js_string_escapes_unsafe_html(self):
        """
        Test escape_js_string escapes &, <, and >, as well as returns a unicode type
        """
        malicious_js_string = "</script><script>alert('hello, ');</script>"

        expected_escaped_js_string = unicode(
            r"\u003C/script\u003E\u003Cscript\u003Ealert(\u0027hello, \u0027)\u003B\u003C/script\u003E"
        )
        escaped_js_string = escape_js_string(malicious_js_string)
        self.assertEquals(expected_escaped_js_string, escaped_js_string)
