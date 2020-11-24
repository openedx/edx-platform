from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.middleware', 'lms.djangoapps.courseware.middleware')

from lms.djangoapps.courseware.middleware import *
