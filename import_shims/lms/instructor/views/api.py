from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.views.api', 'lms.djangoapps.instructor.views.api')

from lms.djangoapps.instructor.views.api import *
