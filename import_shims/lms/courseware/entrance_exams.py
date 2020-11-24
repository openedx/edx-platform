from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.entrance_exams', 'lms.djangoapps.courseware.entrance_exams')

from lms.djangoapps.courseware.entrance_exams import *
