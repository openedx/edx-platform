from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.views.instructor_dashboard', 'lms.djangoapps.instructor.views.instructor_dashboard')

from lms.djangoapps.instructor.views.instructor_dashboard import *
