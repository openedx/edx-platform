from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.fields', 'lms.djangoapps.courseware.fields')

from lms.djangoapps.courseware.fields import *
