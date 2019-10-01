#pylint: disable=missing-docstring
from __future__ import absolute_import

import warnings

if __name__ == 'courseware':
    # pylint: disable=unicode-format-string
    # Show the call stack that imported us wrong.
    msg = "Importing 'lms.djangoapps.courseware' as 'courseware' is no longer supported"
    warnings.warn(msg, DeprecationWarning)
