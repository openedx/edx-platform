from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.views.index', 'lms.djangoapps.courseware.views.index')

from lms.djangoapps.courseware.views.index import *
