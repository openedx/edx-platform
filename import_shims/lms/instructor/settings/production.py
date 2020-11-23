from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.settings.production', 'lms.djangoapps.instructor.settings.production')

from lms.djangoapps.instructor.settings.production import *
