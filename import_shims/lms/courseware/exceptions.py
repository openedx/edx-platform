from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.exceptions', 'lms.djangoapps.courseware.exceptions')

from lms.djangoapps.courseware.exceptions import *
