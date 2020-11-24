from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.settings.devstack', 'lms.djangoapps.instructor.settings.devstack')

from lms.djangoapps.instructor.settings.devstack import *
