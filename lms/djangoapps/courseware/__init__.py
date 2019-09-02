#pylint: disable=missing-docstring
from __future__ import absolute_import

import warnings

if __name__ == 'courseware':
    warnings.warn("Importing 'lms.djangoapps.courseware' as 'courseware' is no longer supported", DeprecationWarning)
