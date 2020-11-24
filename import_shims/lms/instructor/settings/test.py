from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.settings.test', 'lms.djangoapps.instructor.settings.test')

from lms.djangoapps.instructor.settings.test import *
