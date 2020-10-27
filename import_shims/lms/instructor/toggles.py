from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.toggles', 'lms.djangoapps.instructor.toggles')

from lms.djangoapps.instructor.toggles import *
