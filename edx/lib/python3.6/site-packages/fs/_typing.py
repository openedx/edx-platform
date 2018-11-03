"""
Typing objects missing from Python3.5.1

"""
import sys
import six


_PY = sys.version_info

from typing import overload  # type: ignore

if _PY.major == 3 and _PY.minor == 5 and _PY.micro in (0, 1):

    def overload(func):  # pragma: no cover
        return func


try:
    from typing import Text
except ImportError:  # pragma: no cover
    Text = six.text_type  # type: ignore
