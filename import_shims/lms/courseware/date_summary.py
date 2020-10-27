from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.date_summary', 'lms.djangoapps.courseware.date_summary')

from lms.djangoapps.courseware.date_summary import *
