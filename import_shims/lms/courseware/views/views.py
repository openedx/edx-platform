from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.views.views', 'lms.djangoapps.courseware.views.views')

from lms.djangoapps.courseware.views.views import *
