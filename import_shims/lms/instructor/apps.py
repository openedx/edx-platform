from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.apps', 'lms.djangoapps.instructor.apps')

from lms.djangoapps.instructor.apps import *
