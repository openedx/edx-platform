from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.message_types', 'lms.djangoapps.instructor.message_types')

from lms.djangoapps.instructor.message_types import *
