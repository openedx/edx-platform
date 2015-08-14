"""
General testing utilities.
"""
import sys
from contextlib import contextmanager


@contextmanager
def nostderr():
    """
    ContextManager to suppress stderr messages
    http://stackoverflow.com/a/1810086/882918
    """
    savestderr = sys.stderr

    class Devnull(object):
        """ /dev/null incarnation as output-stream-like object """
        def write(self, _):
            """ Write method - just does nothing"""
            pass

    sys.stderr = Devnull()
    try:
        yield
    finally:
        sys.stderr = savestderr
