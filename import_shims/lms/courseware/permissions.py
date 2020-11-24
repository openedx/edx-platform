from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.permissions', 'lms.djangoapps.courseware.permissions')

from lms.djangoapps.courseware.permissions import *
