from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.views.tools', 'lms.djangoapps.instructor.views.tools')

from lms.djangoapps.instructor.views.tools import *
