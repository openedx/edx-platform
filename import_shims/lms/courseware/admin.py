from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.admin', 'lms.djangoapps.courseware.admin')

from lms.djangoapps.courseware.admin import *
