from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.model_data', 'lms.djangoapps.courseware.model_data')

from lms.djangoapps.courseware.model_data import *
