from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.courses', 'lms.djangoapps.courseware.courses')

from lms.djangoapps.courseware.courses import *
