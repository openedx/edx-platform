from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.services', 'lms.djangoapps.courseware.services')

from lms.djangoapps.courseware.services import *
