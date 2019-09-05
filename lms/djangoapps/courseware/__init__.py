#pylint: disable=missing-docstring
from __future__ import absolute_import

import inspect
import warnings

if __name__ == 'courseware':
    # pylint: disable=unicode-format-string
    # Show the call stack that imported us wrong.
    stack = "\n".join("%30s : %s:%d" % (t[3], t[1], t[2]) for t in inspect.stack()[:0:-1])
    msg = "Importing 'lms.djangoapps.courseware' as 'courseware' is no longer supported:\n" + stack
    warnings.warn(msg, DeprecationWarning)
