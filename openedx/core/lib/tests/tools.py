"""
Copy of the useful parts of nose.tools.  This is only used for lettuce test
utility functions, which neither use pytest nor have access to a TestCase
instance.  This module should be deleted once the last lettuce tests have
been ported over to bok-choy.

Tracebacks should not descend into these functions.
We define the ``__unittest`` symbol in their module namespace so unittest will
skip them when printing tracebacks, just as it does for their corresponding
methods in ``unittest`` proper.
"""
import re
import unittest

__all__ = []

# Use the same flag as unittest itself to prevent descent into these functions:
__unittest = 1

# Expose assert* from unittest.TestCase
# - give them pep8 style names
caps = re.compile('([A-Z])')


def pep8(name):
    return caps.sub(lambda m: '_' + m.groups()[0].lower(), name)


class Dummy(unittest.TestCase):
    def noop(self):
        pass


_t = Dummy('noop')

for at in [at for at in dir(_t) if at.startswith('assert') and '_' not in at]:
    pepd = pep8(at)
    vars()[pepd] = getattr(_t, at)
    __all__.append(pepd)

del Dummy
del _t
del pep8
