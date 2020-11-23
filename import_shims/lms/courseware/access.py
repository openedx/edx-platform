from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.access', 'lms.djangoapps.courseware.access')

from lms.djangoapps.courseware.access import *
