from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.context_processor', 'lms.djangoapps.courseware.context_processor')

from lms.djangoapps.courseware.context_processor import *
