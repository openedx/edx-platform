from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.views', 'lms.djangoapps.courseware.views')

from lms.djangoapps.courseware.views import *
