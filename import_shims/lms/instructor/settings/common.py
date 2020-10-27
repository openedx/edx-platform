from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.settings.common', 'lms.djangoapps.instructor.settings.common')

from lms.djangoapps.instructor.settings.common import *
