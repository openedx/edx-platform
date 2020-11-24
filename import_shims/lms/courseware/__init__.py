from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware', 'lms.djangoapps.courseware')

from lms.djangoapps.courseware import *
