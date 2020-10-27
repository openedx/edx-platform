from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.views.gradebook_api', 'lms.djangoapps.instructor.views.gradebook_api')

from lms.djangoapps.instructor.views.gradebook_api import *
