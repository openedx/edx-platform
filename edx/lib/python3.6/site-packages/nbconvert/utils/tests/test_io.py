# encoding: utf-8
"""Tests for utils.io"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import io as stdlib_io
import sys

import pytest

from ..io import unicode_std_stream
from ipython_genutils.py3compat import PY3

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO

def test_UnicodeStdStream():
    # Test wrapping a bytes-level stdout
    if PY3:
        stdoutb = stdlib_io.BytesIO()
        stdout = stdlib_io.TextIOWrapper(stdoutb, encoding='ascii')
    else:
        stdout = stdoutb = stdlib_io.BytesIO()

    orig_stdout = sys.stdout
    sys.stdout = stdout
    try:
        sample = u"@łe¶ŧ←"
        unicode_std_stream().write(sample)

        output = stdoutb.getvalue().decode('utf-8')
        assert output == sample
        assert not stdout.closed
    finally:
        sys.stdout = orig_stdout

@pytest.mark.skipif(not PY3, 
                    reason = "Not applicable on Python 2")
def test_UnicodeStdStream_nowrap():
    # If we replace stdout with a StringIO, it shouldn't get wrapped.
    orig_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        assert unicode_std_stream() is sys.stdout
        assert not sys.stdout.closed
    finally:
        sys.stdout = orig_stdout
