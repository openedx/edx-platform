"""
Tests for json_utils.py
"""
import json
from unittest import TestCase
from openedx.core.lib.json_utils import (
    escape_json_dumps, EscapedEdxJSONEncoder
)


class TestJsonUtils(TestCase):
    """
    Test JSON Utils
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

    def test_escapes_forward_slashes(self):
        """
        Verify that we escape forward slashes with backslashes.
        """
        malicious_json = {'</script><script>alert("hello, ");</script>': '</script><script>alert("world!");</script>'}
        self.assertNotIn(
            '</script>',
            json.dumps(malicious_json, cls=EscapedEdxJSONEncoder)
        )

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
