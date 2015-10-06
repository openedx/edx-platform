"""
Utilities for dealing with Javascript and JSON.
"""
import json
from django.template.defaultfilters import escapejs
from mako.filters import decode
from xmodule.modulestore import EdxJSONEncoder


def _escape_json_for_html(json_str):
    """
    Escape JSON that is safe to be embedded in HTML.

    This implementation is based on escaping performed in simplejson.JSONEncoderForHTML.

    Arguments:
        json_str (str): The JSON string to be escaped

    Returns:
        (str) Escaped JSON that is safe to be embedded in HTML.

    """
    json_str = json_str.replace("&", "\\u0026")
    json_str = json_str.replace(">", "\\u003e")
    json_str = json_str.replace("<", "\\u003c")
    return json_str


def escape_json_dumps(obj, cls=EdxJSONEncoder):
    """
    JSON dumps encoded JSON that is safe to be embedded in HTML.

    Usage:
        Can be used inside a Mako template inside a <SCRIPT> as follows:
            var my_json = ${escape_json_dumps(my_object) | n}

        Use the "n" Mako filter above.  It is possible that the
            default filter may include html encoding in the future, and
            we must make sure to get the proper escaping.

        Ensure ascii in json.dumps (ensure_ascii=True) allows safe skipping of Mako's
            default filter decode.utf8.

    Arguments:
        obj: The json object to be encoded and dumped to a string
        cls (class): The JSON encoder class (defaults to EdxJSONEncoder)

    Returns:
        str: Escaped encoded JSON

    """
    encoded_json = json.dumps(obj, ensure_ascii=True, cls=cls)
    encoded_json = _escape_json_for_html(encoded_json)
    return encoded_json


def escape_js_str(js_str):
    """
    Escape a javascript string that is safe to be embedded in HTML.

    Usage:
        Can be used inside a Mako template inside a <SCRIPT> as follows:
            var my_js_str = "${escape_js_str(my_js_str) | n}"

        Must include the surrounding quotes for the string.

        Use the "n" Mako filter above.  It is possible that the
            default filter may include html encoding in the future, and
            we must make sure to get the proper escaping.

        Mako's default filter decode.utf8 is applied here since this default
            filter is skipped in the Mako template with "n".

    Arguments:
        js_str: The javascript string to be escaped

    Returns:
        str: Escaped javascript as unicode

    """
    js_str = decode.utf8(js_str)
    js_str = escapejs(js_str)
    return js_str
