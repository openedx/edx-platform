# coding: utf-8
"""Test suite for our JSON utilities."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from binascii import a2b_base64
import json

from datetime import datetime
import numbers

import nose.tools as nt

from .. import jsonutil
from ..jsonutil import json_clean, encode_images
from ipython_genutils.py3compat import unicode_to_str

class MyInt(object):
    def __int__(self):
        return 389
numbers.Integral.register(MyInt)

class MyFloat(object):
    def __float__(self):
        return 3.14
numbers.Real.register(MyFloat)


def test():
    # list of input/expected output.  Use None for the expected output if it
    # can be the same as the input.
    pairs = [(1, None), # start with scalars
             (1.0, None),
             ('a', None),
             (True, None),
             (False, None),
             (None, None),
             # Containers
             ([1, 2], None),
             ((1, 2), [1, 2]),
             (set([1, 2]), [1, 2]),
             (dict(x=1), None),
             ({'x': 1, 'y':[1,2,3], '1':'int'}, None),
             # More exotic objects
             ((x for x in range(3)), [0, 1, 2]),
             (iter([1, 2]), [1, 2]),
             (datetime(1991, 7, 3, 12, 00), "1991-07-03T12:00:00.000000"),
             (MyFloat(), 3.14),
             (MyInt(), 389)
             ]
    
    for val, jval in pairs:
        if jval is None:
            jval = val
        out = json_clean(val)
        # validate our cleanup
        assert out == jval
        # and ensure that what we return, indeed encodes cleanly
        json.loads(json.dumps(out))


def test_encode_images():
    # invalid data, but the header and footer are from real files
    pngdata = b'\x89PNG\r\n\x1a\nblahblahnotactuallyvalidIEND\xaeB`\x82'
    jpegdata = b'\xff\xd8\xff\xe0\x00\x10JFIFblahblahjpeg(\xa0\x0f\xff\xd9'
    pdfdata = b'%PDF-1.\ntrailer<</Root<</Pages<</Kids[<</MediaBox[0 0 3 3]>>]>>>>>>'
    bindata = b'\xff\xff\xff\xff'
    
    fmt = {
        'image/png'  : pngdata,
        'image/jpeg' : jpegdata,
        'application/pdf' : pdfdata,
        'application/unrecognized': bindata,
    }
    encoded = json_clean(encode_images(fmt))
    for key, value in fmt.items():
        # encoded has unicode, want bytes
        decoded = a2b_base64(encoded[key])
        assert decoded == value
    encoded2 = json_clean(encode_images(encoded))
    assert encoded == encoded2
    
    # test that we don't double-encode base64 str
    b64_str = {}
    for key, encoded in encoded.items():
        b64_str[key] = unicode_to_str(encoded)
    encoded3 = json_clean(encode_images(b64_str))
    assert encoded3 == b64_str
    for key, value in fmt.items():
        decoded = a2b_base64(encoded3[key])
        assert decoded == value

def test_lambda():
    with nt.assert_raises(ValueError):
        json_clean(lambda : 1)


def test_exception():
    bad_dicts = [{1:'number', '1':'string'},
                 {True:'bool', 'True':'string'},
                 ]
    for d in bad_dicts:
        nt.assert_raises(ValueError, json_clean, d)


def test_unicode_dict():
    data = {u'üniço∂e': u'üniço∂e'}
    clean = jsonutil.json_clean(data)
    assert data == clean
