from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tabs', 'lms.djangoapps.courseware.tabs')

from lms.djangoapps.courseware.tabs import *
